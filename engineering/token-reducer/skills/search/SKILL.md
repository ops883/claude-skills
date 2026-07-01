---
name: "token-reducer-search"
description: "Query an existing token-reducer index for the chunks most relevant to a natural-language question, instead of reading whole files or grepping broadly. Use when: (1) hunting for specific logic in an unfamiliar codebase ('find the auth code'), (2) a research subtask only needs a few relevant snippets, (3) you want to measure how many tokens a full-file read would have cost versus the targeted result."
---

# Token Reducer — Search

Answers a natural-language query against `.cache/index.db`, returning the
top-K most relevant chunks (file path, line range, cosine score, snippet)
instead of full files.

## Command

```bash
python engineering/token-reducer/scripts/context_pipeline.py query \
  --query "Find auth logic" \
  --db .cache/index.db \
  --embedding-backend hash \
  --limit 8 \
  --json
```

Or index + query in one step (useful for ad-hoc, one-off searches):

```bash
python engineering/token-reducer/scripts/context_pipeline.py run \
  --inputs ./src \
  --query "Find auth logic" \
  --embedding-backend hash \
  --db .cache/index.db
```

## How search works

1. Tokenize the query the same way chunks were tokenized at index time
   (lowercase, strip stopwords, `[A-Za-z_][A-Za-z0-9_]+` tokens).
2. Embed the query with the same backend used at index time.
3. Score every indexed chunk by cosine similarity against the query vector.
4. Return the top `--limit` chunks, sorted by score, with a `token_count`
   per chunk so you can see exactly how much context you're spending.

## Reading the output

```json
{
  "query": "Find auth logic",
  "hits": [
    {
      "path": "/abs/path/src/auth.py",
      "start_line": 1,
      "end_line": 42,
      "score": 0.6123,
      "token_count": 118,
      "snippet": "class AuthService: ..."
    }
  ]
}
```

`score` is a heuristic (deterministic hashing/IDF), not a semantic-ML
guarantee. Treat a low top score (roughly < 0.1) as "probably not indexed"
rather than "definitely not in the codebase" — consider rephrasing the
query or widening `--inputs` at index time.

## When to use this vs. Grep/Glob/Read

| Situation | Use |
|---|---|
| "Find the logic that does X" in an unfamiliar area | `token-reducer search` |
| You already know the exact file/symbol name | `Grep`/`Glob` directly — faster, no index needed |
| You need the *entire* file for editing | `Read` the file — don't rely on chunk snippets alone |
| Quick one-off search in a small directory | `run` (index + query combined) |

## Anti-Patterns

- **Don't skip verification.** Always confirm a promising hit by reading
  the actual file at that line range before citing it as fact.
- **Don't rely on a stale index.** If files changed since the last `index`
  run, re-index before trusting "no results" as "doesn't exist".
- **Don't use this for exact-symbol lookups.** `Grep "def my_function"` is
  faster and exact; this tool is for fuzzy, natural-language questions.

## Cross-References

- `engineering/token-reducer/skills/index/SKILL.md` — building the index queried here
- `engineering/token-reducer/skills/stats/SKILL.md` — index size/health
- `engineering/token-reducer/agents/context-scout.md` — sub-agent that wraps this workflow
- `engineering/token-reducer/SKILL.md` — parent skill overview
