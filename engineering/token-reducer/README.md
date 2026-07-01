# Token Reducer

Deterministic, stdlib-only context retrieval for Claude Code. Indexes a
codebase into a local SQLite cache, then answers natural-language queries
with just the relevant chunks — instead of loading whole files or
directories into an LLM's context window.

> Don't read what you can search.

## Why

Reading a 2,000-line file to answer "where is the auth logic" costs every
line of that file, including the 95% that isn't auth logic. Token Reducer
indexes once, then returns only the handful of chunks that actually match
a query — with the file path, line range, and a score, so you can go read
exactly the right spot if you need more.

## Install

### Claude Code (Plugin)
```
/plugin marketplace add alirezarezvani/claude-skills
/plugin install token-reducer@claude-code-skills
```

### Manual (CLI only, no plugin install)
```bash
python engineering/token-reducer/scripts/context_pipeline.py --help
```

No dependencies to install — the default `hash` embedding backend is pure
Python standard library.

## Usage

```bash
# Index a directory, then search it in one step
python scripts/context_pipeline.py run \
  --inputs ./src \
  --query "Find auth logic" \
  --embedding-backend hash \
  --db .cache/index.db

# Build/refresh the index (incremental — unchanged files are skipped)
python scripts/context_pipeline.py index --inputs ./src ./lib --db .cache/index.db

# Query an existing index
python scripts/context_pipeline.py query --query "rate limiting" --db .cache/index.db --json

# Check index size and estimated token footprint
python scripts/context_pipeline.py stats --db .cache/index.db
```

Inside Claude Code, the same flows are available as slash commands:
`/tr:index`, `/tr:search`, `/tr:stats`.

## How it works

1. **Chunk** — files are split into ~60-line windows with 10-line overlap.
2. **Embed** — each chunk gets a deterministic vector via a hashing trick
   (default backend `hash`), optionally weighted by corpus IDF (`tfidf`).
   No ML models, no API calls, no network access — the same input always
   produces the same output.
3. **Cache** — chunks + vectors are stored in SQLite. Re-indexing is
   incremental: files are re-chunked only if their SHA-1 changed.
4. **Search** — a query is tokenized/embedded the same way, scored against
   every cached chunk by cosine similarity, and the top-K matches are
   returned with `path`, `start_line`, `end_line`, `score`, and `snippet`.

## Components

| Path | Purpose |
|---|---|
| `scripts/context_pipeline.py` | Core CLI — `index`, `run`, `query`, `stats` |
| `scripts/mcp_server.py` | **Experimental** MCP stdio server exposing `search_context` — see caveat below |
| `hooks/suggest-search.sh` | `PostToolUse` (Read) hook that nudges toward `/tr:search` after a large full-file read |
| `agents/context-scout.md` | Read-only sub-agent: searches before it sweeps, verifies every hit |
| `commands/tr-*.md` | `/tr:index`, `/tr:search`, `/tr:stats` |
| `skills/index`, `skills/search`, `skills/stats` | Focused sub-skill docs for each capability |
| `evals/` | Deterministic eval: indexes fixture files, checks the top hit for a known query |

## MCP server — experimental

`scripts/mcp_server.py` implements just enough of the MCP stdio transport
(line-delimited JSON-RPC 2.0: `initialize`, `tools/list`, `tools/call`) to
expose search as a `search_context` tool. **It has not been tested against
a live MCP client.** The CLI (`context_pipeline.py`) is the verified
interface — treat the MCP server as a reference implementation to adapt,
and confirm it against your specific client before relying on it.

## Configuration

Everything works with zero configuration. Optional environment variables
(see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `TOKEN_REDUCER_DB` | `.cache/index.db` | Default index path |
| `TOKEN_REDUCER_EMBEDDING_BACKEND` | `hash` | Default backend (`hash` or `tfidf`) |

`requirements-optional.txt` documents one purely optional dependency
(`numpy`) for accelerating similarity search on very large indexes — not
required, and not imported by default.

## Limitations

- **Heuristic, not semantic.** The `hash`/`tfidf` backends are deterministic
  bag-of-words retrieval, not a trained embedding model. They're good at
  "which file mentions these words in this pattern", not true semantic
  meaning. Always verify a hit before citing it as fact.
- **Pure-Python similarity search.** Cosine scoring loops over every chunk
  in Python; fine for typical project sizes, may get slow well past
  ~50k chunks (see `requirements-optional.txt`).
- **Extension allow-list.** Only common code/doc extensions are indexed by
  default — pass `--extensions` to widen or narrow this.

## Related

- [llm-wiki](../llm-wiki/) — a related "don't re-derive knowledge" pattern, but for accumulated research rather than live codebase search
- [self-improving-agent](../../engineering-team/self-improving-agent/) — sister plugin pattern (hooks + commands + agents) this plugin's structure follows
