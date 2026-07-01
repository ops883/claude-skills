---
name: tr-stats
description: Show token-reducer index size and an estimated token footprint, to gauge whether indexing is paying off. Usage /tr-stats
---

# /tr:stats

Report the current state of the token-reducer index: files indexed, chunks
indexed, and an estimated token count of everything cached — useful for
sanity-checking that indexing actually ran, and roughly how much context a
full-file read of the same material would have cost.

## Usage

```
/tr:stats
```

## What happens

1. Runs `scripts/context_pipeline.py stats --db .cache/index.db --json`
2. Reports files indexed, chunks indexed, estimated tokens indexed, and the active embedding backend
3. If the index doesn't exist yet, reports zero counts and suggests `/tr:index`

## Scripts

- `engineering/token-reducer/scripts/context_pipeline.py` — indexing + search engine

## Skill Reference

→ `engineering/token-reducer/SKILL.md`
→ `engineering/token-reducer/skills/stats/SKILL.md`
