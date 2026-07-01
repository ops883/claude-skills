---
name: "token-reducer-index"
description: "Build or update the token-reducer SQLite index for a set of files/directories, using a deterministic hashing-trick embedding (no ML/LLM calls). Use when: (1) starting work in a codebase you haven't indexed yet, (2) after a batch of edits, before relying on token-reducer search, (3) you want incremental re-indexing that skips unchanged files."
---

# Token Reducer — Index

Builds (or incrementally updates) `.cache/index.db`: a local SQLite cache of
chunked source files with per-chunk deterministic embeddings, used by the
`search` sub-skill to answer queries without reading whole files.

## Command

```bash
python engineering/token-reducer/scripts/context_pipeline.py index \
  --inputs ./src ./lib \
  --db .cache/index.db \
  --embedding-backend hash
```

## How indexing works

1. **Walk** each input path, skipping `SKIP_DIRS` (`.git`, `node_modules`,
   `__pycache__`, `.venv`, `dist`, `build`, etc.) and files over ~1 MB.
2. **Hash** each file's content (SHA-1). If the hash matches what's already
   in `files.sha1`, the file is skipped — indexing is incremental.
3. **Chunk** changed/new files into ~60-line windows with 10-line overlap
   (`CHUNK_LINES` / `CHUNK_OVERLAP` in `context_pipeline.py`), so a match
   near a chunk boundary still surfaces.
4. **Embed** each chunk with the chosen backend:
   - `hash` (default) — a deterministic hashing-trick bag-of-words vector.
     Zero setup, works on the very first file indexed.
   - `tfidf` — the same hashing trick, weighted by corpus IDF computed from
     chunks already in the index. Slightly sharper on larger, more
     repetitive codebases; requires an existing index to compute IDF from.
5. **Write** chunks + packed float vectors to SQLite (`chunks` table) and
   update the `files` row (path, sha1, mtime, indexed_at).

No network calls, no ML libraries, no LLM calls — every run is
deterministic and reproducible.

## Flags worth knowing

| Flag | Default | Purpose |
|---|---|---|
| `--extensions` | code + docs (`.py .js .ts .go .md ...`) | Narrow or widen what gets indexed |
| `--chunk-lines` / `--chunk-overlap` | `60` / `10` | Trade recall vs. index size |
| `--force` | off | Re-index even if the content hash is unchanged |
| `--embedding-backend` | `hash` | Switch to `tfidf` once an index already exists |

## Anti-Patterns

- **Don't re-index on every query.** Indexing is incremental and cheap, but
  unnecessary re-runs still cost a filesystem walk. Index once per session
  or after a real batch of edits.
- **Don't index generated/vendor directories.** They're already skipped by
  default (`SKIP_DIRS`), but if you widen `--extensions`, watch for
  `dist/`, `vendor/`, lockfiles, etc. sneaking back in.
- **Don't treat the index as a source of truth.** It's a retrieval aid —
  always verify a hit by reading the actual file/line range before citing it.

## Cross-References

- `engineering/token-reducer/skills/search/SKILL.md` — querying the index built here
- `engineering/token-reducer/skills/stats/SKILL.md` — checking index size/health
- `engineering/token-reducer/SKILL.md` — parent skill overview
