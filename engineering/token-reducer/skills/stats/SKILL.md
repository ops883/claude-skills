---
name: "token-reducer-stats"
description: "Report token-reducer index size and an estimated token footprint of everything cached, to sanity-check indexing and gauge token savings. Use when: (1) confirming an /tr:index run actually indexed the expected files, (2) deciding whether the index is large enough to be worth querying, (3) reporting how much context a full-file read of the same material would have cost."
---

# Token Reducer — Stats

Reports the current state of `.cache/index.db`.

## Command

```bash
python engineering/token-reducer/scripts/context_pipeline.py stats \
  --db .cache/index.db \
  --json
```

## Output fields

| Field | Meaning |
|---|---|
| `files_indexed` | Distinct files currently tracked in the index |
| `chunks_indexed` | Total chunk rows (each ~60 lines, 10-line overlap) |
| `indexed_chars` | Total characters across all chunk text |
| `indexed_tokens_estimate` | `indexed_chars / 4` — a rough token estimate |
| `embedding_backend` | Backend used for the most recent `index` run (`hash` or `tfidf`) |

## Using this to reason about savings

`indexed_tokens_estimate` is the cost of indexing everything **once**, not
the cost of a search. A single `search` call typically returns 5-10 small
chunks (hundreds to low thousands of tokens) rather than the full indexed
corpus — that gap is the token savings versus reading whole files directly.

If `files_indexed` is `0`, no index exists yet — run `/tr:index` first.

## Anti-Patterns

- Don't treat `indexed_tokens_estimate` as what a query costs — it's the
  size of the whole cache, not a single search result.
- Don't skip this check before debugging "search returns nothing" — an
  empty or tiny index is the most common cause.

## Cross-References

- `engineering/token-reducer/skills/index/SKILL.md` — building the index
- `engineering/token-reducer/skills/search/SKILL.md` — querying the index
- `engineering/token-reducer/SKILL.md` — parent skill overview
