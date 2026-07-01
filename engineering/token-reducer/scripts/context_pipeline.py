#!/usr/bin/env python3
"""
context_pipeline.py — deterministic, stdlib-only context retrieval for
reducing LLM token usage.

Indexes source files into a local SQLite cache, then answers natural-
language queries by returning only the most relevant chunks — instead of
loading whole files/directories into an LLM's context window. No ML/LLM
calls: embeddings are computed with a deterministic hashing trick (and an
optional corpus-IDF weighting), matching this repo's "algorithm over AI"
convention.

Subcommands:
    index   Build/update the index for one or more input paths.
    run     index + query in one step (convenience for ad-hoc use).
    query   Query an existing index without re-indexing.
    stats   Show index size and an estimated token footprint.

Examples:
    python context_pipeline.py run --inputs ./src --query "Find auth logic" \\
        --embedding-backend hash --db .cache/index.db

    python context_pipeline.py index --inputs ./src ./lib --db .cache/index.db
    python context_pipeline.py query --query "rate limiting" --db .cache/index.db --json
    python context_pipeline.py stats --db .cache/index.db
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import struct
import sys
import time
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Config — environment variables are optional; the CLI runs with zero setup.
# ---------------------------------------------------------------------------

DEFAULT_DB = os.environ.get("TOKEN_REDUCER_DB", ".cache/index.db")
DEFAULT_BACKEND = os.environ.get("TOKEN_REDUCER_EMBEDDING_BACKEND", "hash")

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
    ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".kt", ".scala",
    ".md", ".sql", ".sh", ".yaml", ".yml", ".json",
}
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", ".cache", "target", "vendor", ".mypy_cache", ".pytest_cache",
}
MAX_FILE_BYTES = 1_000_000  # skip anything bigger — not worth indexing whole
CHUNK_LINES = 60
CHUNK_OVERLAP = 10
HASH_DIMS = 256
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "to", "of",
    "in", "on", "at", "for", "by", "with", "from", "is", "are", "was",
    "were", "be", "been", "being", "this", "that", "these", "those", "it",
    "its", "as", "we", "you", "they", "their", "our", "us", "not", "no",
    "do", "does", "did", "will", "would", "can", "could", "should", "find",
}

# ---------------------------------------------------------------------------
# Tokenization + embeddings (stdlib only — no ML/LLM calls)
# ---------------------------------------------------------------------------


def split_identifier(token: str) -> list[str]:
    """Split a snake_case/camelCase/PascalCase identifier into sub-words,
    so a query like "auth" can match code that only ever spells it as
    AuthService/hash_password rather than the bare word "auth"."""
    parts = []
    for piece in token.split("_"):
        if piece:
            parts.extend(p for p in CAMEL_BOUNDARY_RE.split(piece) if p)
    return parts


def tokenize(text: str) -> list[str]:
    out = []
    for raw in TOKEN_RE.findall(text):
        low = raw.lower()
        if low not in STOPWORDS and len(low) > 1:
            out.append(low)
        for sub in split_identifier(raw):
            sub_low = sub.lower()
            if sub_low != low and sub_low not in STOPWORDS and len(sub_low) > 1:
                out.append(sub_low)
    return out


def hash_embed(tokens: list[str], dims: int = HASH_DIMS) -> list[float]:
    """Deterministic 'hashing trick' bag-of-words vector. No ML deps."""
    vec = [0.0] * dims
    for tok, count in Counter(tokens).items():
        h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=8).hexdigest(), 16)
        idx = h % dims
        sign = 1.0 if (h // dims) % 2 == 0 else -1.0
        vec[idx] += sign * count
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def tfidf_embed(tokens: list[str], idf: dict, dims: int = HASH_DIMS) -> list[float]:
    """Hashing-trick vector weighted by corpus IDF. Needs an existing index
    to compute IDF from — slightly better precision than plain hashing on
    larger, more repetitive codebases."""
    vec = [0.0] * dims
    for tok, count in Counter(tokens).items():
        h = int(hashlib.blake2b(tok.encode("utf-8"), digest_size=8).hexdigest(), 16)
        idx = h % dims
        sign = 1.0 if (h // dims) % 2 == 0 else -1.0
        weight = count * idf.get(tok, 1.0)
        vec[idx] += sign * weight
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def pack_vector(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def unpack_vector(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def embed(tokens: list[str], backend: str, idf: dict | None = None) -> list[float]:
    if backend == "hash":
        return hash_embed(tokens)
    if backend == "tfidf":
        return tfidf_embed(tokens, idf or {})
    raise ValueError(f"unknown embedding backend: {backend}")


# ---------------------------------------------------------------------------
# Filesystem walk + chunking
# ---------------------------------------------------------------------------


def iter_source_files(inputs: list[str], extensions: set):
    for raw in inputs:
        root = Path(raw).expanduser().resolve()
        if root.is_file():
            if root.suffix in extensions:
                yield root
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix not in extensions:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path


def chunk_lines(text: str, size: int = CHUNK_LINES, overlap: int = CHUNK_OVERLAP):
    lines = text.splitlines()
    if not lines:
        return
    step = max(size - overlap, 1)
    for start in range(0, len(lines), step):
        end = min(start + size, len(lines))
        chunk = "\n".join(lines[start:end])
        if chunk.strip():
            yield start + 1, end, chunk
        if end == len(lines):
            break


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    h.update(path.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# SQLite index
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    sha1 TEXT NOT NULL,
    mtime REAL NOT NULL,
    indexed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    vector BLOB NOT NULL,
    FOREIGN KEY (path) REFERENCES files(path)
);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def open_db(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.executescript(SCHEMA)
    return conn


def build_idf(conn: sqlite3.Connection) -> dict:
    """Corpus IDF over already-indexed chunk text — used by the tfidf backend."""
    rows = conn.execute("SELECT text FROM chunks").fetchall()
    n = len(rows)
    if n == 0:
        return {}
    df: Counter = Counter()
    for (text,) in rows:
        for tok in set(tokenize(text)):
            df[tok] += 1
    return {tok: math.log(1 + n / c) for tok, c in df.items()}


def index_paths(conn: sqlite3.Connection, inputs: list[str], extensions: set,
                 backend: str, chunk_size: int, overlap: int, force: bool = False) -> dict:
    stats = {"files_scanned": 0, "files_indexed": 0, "files_unchanged": 0, "chunks_written": 0}
    idf: dict = build_idf(conn) if backend == "tfidf" else {}

    for path in iter_source_files(inputs, extensions):
        stats["files_scanned"] += 1
        rel = str(path)
        sha1 = file_sha1(path)
        row = conn.execute("SELECT sha1 FROM files WHERE path = ?", (rel,)).fetchone()
        if row and row[0] == sha1 and not force:
            stats["files_unchanged"] += 1
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        conn.execute("DELETE FROM chunks WHERE path = ?", (rel,))
        for start, end, chunk in chunk_lines(text, chunk_size, overlap):
            tokens = tokenize(chunk)
            vec = embed(tokens, backend, idf)
            conn.execute(
                "INSERT INTO chunks (path, start_line, end_line, text, token_count, vector) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rel, start, end, chunk, len(tokens), pack_vector(vec)),
            )
            stats["chunks_written"] += 1

        conn.execute(
            "INSERT INTO files (path, sha1, mtime, indexed_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(path) DO UPDATE SET sha1=excluded.sha1, mtime=excluded.mtime, "
            "indexed_at=excluded.indexed_at",
            (rel, sha1, path.stat().st_mtime, time.time()),
        )
        stats["files_indexed"] += 1

    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('embedding_backend', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (backend,),
    )
    conn.commit()
    return stats


def query_index(conn: sqlite3.Connection, query: str, backend: str, limit: int) -> list[dict]:
    idf: dict = build_idf(conn) if backend == "tfidf" else {}
    qtokens = tokenize(query)
    if not qtokens:
        return []
    qvec = embed(qtokens, backend, idf)

    hits = []
    for path, start, end, text, tok_count, blob in conn.execute(
        "SELECT path, start_line, end_line, text, token_count, vector FROM chunks"
    ):
        vec = unpack_vector(blob)
        score = cosine(qvec, vec)
        if score > 0:
            hits.append((score, path, start, end, text, tok_count))

    hits.sort(key=lambda h: h[0], reverse=True)
    results = []
    for score, path, start, end, text, tok_count in hits[:limit]:
        results.append({
            "path": path,
            "start_line": start,
            "end_line": end,
            "score": round(score, 4),
            "token_count": tok_count,
            "snippet": text if len(text) <= 600 else text[:600] + "…",
        })
    return results


def estimate_tokens(chars: int) -> int:
    # Rough heuristic (~4 chars/token for source code); matches common estimators.
    return max(0, chars // 4)


def stats_report(conn: sqlite3.Connection) -> dict:
    n_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    n_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    total_chars = conn.execute("SELECT COALESCE(SUM(LENGTH(text)),0) FROM chunks").fetchone()[0]
    backend_row = conn.execute("SELECT value FROM meta WHERE key='embedding_backend'").fetchone()
    return {
        "files_indexed": n_files,
        "chunks_indexed": n_chunks,
        "indexed_chars": total_chars,
        "indexed_tokens_estimate": estimate_tokens(total_chars),
        "embedding_backend": backend_row[0] if backend_row else None,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_json_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON")


def add_common_index_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--inputs", nargs="+", required=True, help="Files/directories to index")
    p.add_argument("--db", default=DEFAULT_DB, help=f"SQLite index path (default: {DEFAULT_DB})")
    p.add_argument("--embedding-backend", choices=["hash", "tfidf"], default=DEFAULT_BACKEND)
    p.add_argument("--extensions", nargs="*", default=None,
                    help="Override the default set of file extensions to index")
    p.add_argument("--chunk-lines", type=int, default=CHUNK_LINES)
    p.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)
    p.add_argument("--force", action="store_true", help="Re-index unchanged files")


def add_query_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--query", required=True, help="Natural-language query")
    p.add_argument("--limit", type=int, default=8, help="Max results to return")


def cmd_index(args: argparse.Namespace) -> int:
    conn = open_db(args.db)
    extensions = set(args.extensions) if args.extensions else DEFAULT_EXTENSIONS
    stats = index_paths(conn, args.inputs, extensions, args.embedding_backend,
                         args.chunk_lines, args.chunk_overlap, args.force)
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(f"Indexed {stats['files_indexed']} files "
              f"({stats['files_unchanged']} unchanged, {stats['chunks_written']} chunks) "
              f"-> {args.db}")
    if stats["files_scanned"] == 0:
        print("[warn] no matching files found under --inputs", file=sys.stderr)
        return 1
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    conn = open_db(args.db)
    n_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    if n_chunks == 0:
        print(f"[error] index at {args.db} is empty — run 'index' first", file=sys.stderr)
        return 2
    results = query_index(conn, args.query, args.embedding_backend, args.limit)
    _print_results(args.query, results, args.json)
    return 0 if results else 1


def cmd_run(args: argparse.Namespace) -> int:
    conn = open_db(args.db)
    extensions = set(args.extensions) if args.extensions else DEFAULT_EXTENSIONS
    index_paths(conn, args.inputs, extensions, args.embedding_backend,
                args.chunk_lines, args.chunk_overlap, args.force)
    results = query_index(conn, args.query, args.embedding_backend, args.limit)
    _print_results(args.query, results, args.json)
    return 0 if results else 1


def cmd_stats(args: argparse.Namespace) -> int:
    conn = open_db(args.db)
    report = stats_report(conn)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Index: {args.db}")
        print(f"  Files indexed:     {report['files_indexed']}")
        print(f"  Chunks indexed:    {report['chunks_indexed']}")
        print(f"  ~Tokens indexed:   {report['indexed_tokens_estimate']:,}")
        print(f"  Embedding backend: {report['embedding_backend']}")
    return 0


def _print_results(query: str, results: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"query": query, "hits": results}, indent=2, ensure_ascii=False))
        return
    if not results:
        print(f"No matches for: {query}")
        return
    total_tokens = sum(r["token_count"] for r in results)
    print(f"Query: {query}  ({len(results)} hits, ~{total_tokens} tokens returned)")
    for r in results:
        print(f"\n  [{r['score']}] {r['path']}:{r['start_line']}-{r['end_line']}  (~{r['token_count']} tok)")
        for line in r["snippet"].splitlines()[:6]:
            print(f"     {line}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="context_pipeline.py",
        description="Deterministic, stdlib-only context retrieval for reducing LLM token usage.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Build/update the index for --inputs")
    add_common_index_args(p_index)
    add_json_arg(p_index)
    p_index.set_defaults(func=cmd_index)

    p_run = sub.add_parser("run", help="Index --inputs, then answer --query")
    add_common_index_args(p_run)
    add_query_args(p_run)
    add_json_arg(p_run)
    p_run.set_defaults(func=cmd_run)

    p_query = sub.add_parser("query", help="Query an existing --db without re-indexing")
    p_query.add_argument("--db", default=DEFAULT_DB)
    p_query.add_argument("--embedding-backend", choices=["hash", "tfidf"], default=DEFAULT_BACKEND)
    add_query_args(p_query)
    add_json_arg(p_query)
    p_query.set_defaults(func=cmd_query)

    p_stats = sub.add_parser("stats", help="Show index size and estimated token footprint")
    p_stats.add_argument("--db", default=DEFAULT_DB)
    add_json_arg(p_stats)
    p_stats.set_defaults(func=cmd_stats)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.func(args)
    except Exception as exc:  # deterministic CLI: surface errors, never fail silently
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(2)
    sys.exit(code)


if __name__ == "__main__":
    main()
