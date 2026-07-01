# Token Reducer — Claude Code Instructions

This plugin gives you an indexed, deterministic way to answer "where is X
in this codebase" without reading whole files.

## Commands

Use the `/tr:` namespace for all commands:

- `/tr:index <path>` — build/update the index for one or more paths
- `/tr:search "<query>"` — return the top matching chunks for a query
- `/tr:stats` — report index size and estimated token footprint

## When to reach for this

- You're about to `Read` an unfamiliar file just to find one function or
  concept in it → search first, read the specific hit instead.
- A sub-task only needs "where is the retry logic" or "find the webhook
  signature check" → spawn `agents/context-scout.md` rather than doing a
  broad `Grep -r` + multiple full-file `Read`s yourself.
- You want to gauge whether context-gathering in a session is expensive →
  `/tr:stats` shows the indexed token footprint; a `/tr:search` result set
  is typically a small fraction of that.

## When NOT to reach for this

- You already know the exact file or symbol name — `Grep`/`Glob` is faster
  and exact; don't index first.
- You need to edit a file — `Read` it directly once you've located it via
  search; don't edit from a chunk snippet alone.
- The codebase is tiny (a handful of files) — indexing overhead isn't worth
  it; just read the files.

## Key principle

**Search before you sweep.** Every `Grep -r` across a large tree or full-file
`Read` "just to see what's in there" is a token bill. If the goal is
locating specific logic rather than reading a known file end-to-end, index
once and query instead.

## Agents

- **context-scout**: read-only sub-agent spawned for "find X in the
  codebase" research questions. Always searches the index before falling
  back to a broader sweep, and verifies every hit by reading the actual
  line range before reporting it.

## Hooks

The `suggest-search.sh` hook fires on `PostToolUse` (Read only). It checks
whether the just-completed read was large (~2,000+ tokens) and, if so,
prints a short nudge toward `/tr:search` for next time. Zero overhead on
small reads.

When you install this plugin via
`/plugin install token-reducer@claude-code-skills`, the hook is registered
automatically from `hooks/hooks.json` — no manual configuration needed.

If you ever need to wire it up by hand (e.g. you copied the skill directly
instead of installing as a plugin), use the `${CLAUDE_PLUGIN_ROOT}`
variable so the path resolves against the plugin root rather than your
current working directory:

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Read",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/hooks/suggest-search.sh"
      }]
    }]
  }
}
```

**Do not use a relative path like `./hooks/suggest-search.sh`** — Claude
Code resolves hook commands against the current working directory, not the
plugin root. A relative path silently fails in any session started outside
the plugin install dir.

## MCP server (experimental)

`.mcp.json` registers `scripts/mcp_server.py` as a stdio MCP server
exposing a single `search_context` tool. This has not been verified
against a live MCP client — prefer driving `scripts/context_pipeline.py`
directly (via Bash or the slash commands above) unless you've confirmed
the MCP path works in your environment.
