#!/usr/bin/env python3
"""
run_evals.py — tiny, deterministic eval harness for context_pipeline.py.

Indexes evals/fixtures/sample_src/ into a throwaway SQLite db, runs the
query defined in each evals/expected/*.json spec, and checks that the top
hit is the expected file. No network, no ML, no external deps — stdlib
only, consistent with the rest of this plugin.

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import context_pipeline as cp  # noqa: E402

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "sample_src"
EXPECTED_DIR = ROOT / "expected"


def run_one(expected_path: Path, db_path: Path) -> dict:
    spec = json.loads(expected_path.read_text())
    conn = cp.open_db(str(db_path))
    cp.index_paths(conn, [str(FIXTURES)], cp.DEFAULT_EXTENSIONS, "hash",
                    cp.CHUNK_LINES, cp.CHUNK_OVERLAP)
    hits = cp.query_index(conn, spec["query"], "hash", limit=5)

    passed = bool(hits) and spec["top_file_must_contain"] in hits[0]["path"]
    if passed and "min_score" in spec:
        passed = hits[0]["score"] >= spec["min_score"]

    return {
        "name": expected_path.stem,
        "query": spec["query"],
        "passed": passed,
        "top_hit": hits[0]["path"] if hits else None,
        "top_score": hits[0]["score"] if hits else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run token-reducer evals")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "eval_index.db"
        results = [run_one(f, db_path) for f in sorted(EXPECTED_DIR.glob("*.json"))]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"[{status}] {r['name']}: \"{r['query']}\" -> {r['top_hit']} (score={r['top_score']})")

    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n{len(failures)}/{len(results)} evals failed", file=sys.stderr)
        sys.exit(1)

    if not args.json:
        print(f"\n{len(results)}/{len(results)} evals passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
