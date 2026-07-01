---
name: tr-index
description: Build or update the token-reducer index for one or more paths, so later /tr:search calls return relevant chunks instead of full files. Usage /tr-index <path> [<path>...]
---

# /tr:index

Index one or more files or directories into the token-reducer cache
(`.cache/index.db` by default). Indexing is incremental — files whose
content hash hasn't changed since the last run are skipped, so re-running
`/tr:index` after a small edit is cheap.

## Usage

```
/tr:index <path> [<path>...]
/tr:index ./src
/tr:index ./src ./lib --force
```

## What happens

1. Runs `scripts/context_pipeline.py index --inputs <path>... --db .cache/index.db`
2. Reports files scanned, files (re)indexed, files unchanged, and chunks written
3. If nothing matched the default extension list, warns and suggests `--extensions`

## Scripts

- `engineering/token-reducer/scripts/context_pipeline.py` — indexing + search engine

## Rules

- Run this once per project (or after a large batch of edits) before relying on `/tr:search`.
- The index lives at `.cache/index.db` by default — safe to `.gitignore`, cheap to rebuild.
- Pass `--force` only when you suspect the cache is stale despite unchanged file hashes (rare).

## Skill Reference

→ `engineering/token-reducer/SKILL.md`
→ `engineering/token-reducer/skills/index/SKILL.md`
