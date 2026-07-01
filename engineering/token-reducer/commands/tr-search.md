---
name: tr-search
description: Query the token-reducer index for the chunks most relevant to a natural-language question, instead of reading whole files. Usage /tr-search "<query>"
---

# /tr:search

Answer a natural-language query using the existing token-reducer index —
returns only the top matching chunks (file path, line range, snippet)
instead of full files.

## Usage

```
/tr:search "<query>"
/tr:search "Find auth logic"
/tr:search "where is rate limiting implemented" --limit 5
```

## What happens

1. Runs `scripts/context_pipeline.py query --query "<query>" --db .cache/index.db --json`
2. If the index is empty, reports the error and suggests running `/tr:index` first
3. Reads only the returned chunks — **not** the full files they came from — unless a hit clearly needs more surrounding context, in which case Read the specific file at that line range

## Scripts

- `engineering/token-reducer/scripts/context_pipeline.py` — indexing + search engine

## Rules

- Prefer this over `Grep`/`Glob`/`Read` sweeps when the goal is "find the logic that does X", not "read this specific known file".
- If results look thin or off-topic, the index may be stale — run `/tr:index` again before concluding nothing exists.
- This is a heuristic search (deterministic hashing/IDF, not semantic ML), not a certainty. Verify a hit before making claims about it.

## Skill Reference

→ `engineering/token-reducer/SKILL.md`
→ `engineering/token-reducer/skills/search/SKILL.md`
