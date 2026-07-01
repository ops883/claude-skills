---
name: "token-reducer"
description: "Index a codebase into a local SQLite cache and answer natural-language queries with just the relevant chunks, instead of loading whole files/directories into context. Use when: (1) exploring an unfamiliar or large codebase before reading files directly, (2) a research subtask only needs specific logic (e.g. 'find the auth code') rather than full files, (3) you want to measure or reduce the token cost of context-gathering across a session."
---

# Token Reducer

> Don't read what you can search.

Every time an agent reads a whole file to answer "where is X", it pays for
every line of that file — including the 95% that isn't X. Token Reducer
indexes a codebase once into a local SQLite cache, then answers targeted
queries with just the handful of chunks that actually matter.

## Quick Reference

| Command | What it does |
|---|---|
| `/tr:index <path>` | Build/update the index for one or more paths (incremental) |
| `/tr:search "<query>"` | Return the top matching chunks for a natural-language query |
| `/tr:stats` | Report index size and estimated token footprint |

Or drive the CLI directly:

```bash
python scripts/context_pipeline.py run \
  --inputs ./src \
  --query "Find auth logic" \
  --embedding-backend hash \
  --db .cache/index.db
```

## How it works

1. **Chunk** — files under `--inputs` are split into ~60-line windows with
   10-line overlap.
2. **Embed** — each chunk gets a deterministic vector via a hashing trick
   (`--embedding-backend hash`), optionally weighted by corpus IDF
   (`tfidf`). No ML models, no API calls — same input always produces the
   same output.
3. **Cache** — chunks + vectors land in SQLite (`.cache/index.db` by
   default). Re-indexing is incremental: unchanged files (by SHA-1) are
   skipped.
4. **Search** — a query is tokenized and embedded the same way, then
   scored against every chunk by cosine similarity. The top-K chunks come
   back with file path, line range, score, and a snippet.

Everything runs with the Python standard library only — no pip installs
required for the default `hash` backend (see `requirements-optional.txt`
for a purely optional acceleration path at very large scale).

## When to use this vs. reading files directly

| Situation | Use |
|---|---|
| "Find the logic that does X" in unfamiliar code | Token Reducer search |
| You already know the exact file or symbol name | `Grep`/`Glob` directly |
| You need the whole file to edit it | `Read` the file |
| A research sub-task should stay read-only and token-frugal | Spawn `agents/context-scout.md` |

## Components

- **`scripts/context_pipeline.py`** — the CLI: `index`, `run`, `query`, `stats`
- **`scripts/mcp_server.py`** — experimental MCP stdio server exposing `search_context` as a tool (see README for status/caveats)
- **`hooks/suggest-search.sh`** — `PostToolUse` hook on `Read`; nudges toward `/tr:search` after a large full-file read
- **`agents/context-scout.md`** — read-only sub-agent that searches before it sweeps, and verifies every hit
- **`commands/`** — `/tr:index`, `/tr:search`, `/tr:stats`
- **`evals/`** — a tiny, deterministic eval that indexes fixture files and checks the top hit for a known query

## Anti-Patterns

- **Don't index and forget.** An index built once and never refreshed will
  silently miss recent edits — re-run `/tr:index` after meaningful changes.
- **Don't trust a single low-score hit as fact.** This is heuristic
  retrieval (hashing/IDF), not semantic ML — verify by reading the cited
  line range before making claims.
- **Don't use this for exact-symbol lookups.** `Grep "def handler"` beats
  a fuzzy search when you already know the exact string.
- **Don't wire the MCP server into anything you haven't tested.** It's
  labeled experimental for a reason — the CLI is the verified interface.

## Cross-References

- `engineering/token-reducer/skills/index/SKILL.md`
- `engineering/token-reducer/skills/search/SKILL.md`
- `engineering/token-reducer/skills/stats/SKILL.md`
- `engineering/llm-wiki/` — a related "reduce re-derivation" pattern, but for accumulated knowledge rather than live codebase search
