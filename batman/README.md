# batman — remote-standardized profile

Francisco Guerrero's unified AI assistant for the Law Offices of José R. Santiago,
**adapted to run lean and mean in a Claude Code remote session** (cloud container),
not on the firm's Mac.

## What "remote-standardized" changes

The desktop batman routes to local repos on Francisco's machine (`/Users/tico/agents`,
`headroom`, `claude-for-legal`, `legal-sources`, `ai-lawyer`, a Telegram bot, …).
**None of those exist in an ephemeral remote container.** This profile retires them and
re-points every route to what a remote session actually has — MCP servers and native
tools — so batman never silently degrades into plain-model fallback while *looking*
fully wired.

| Desktop backend (retired) | Remote replacement |
|---|---|
| RUFLO agents (`import agents`) | Reason the frames inline; verify against **CourtListener MCP** |
| `headroom` token-compression proxy | Native discipline — Read `offset`/`limit`, Grep, persisted-output |
| `legal-sources` / `claude-for-legal` | **CourtListener MCP** + targeted WebFetch of primary sources |
| Local firm files (`Law_Offices_Santiago/`) | **Google Drive MCP** (`search_files`, `read_file_content`) |
| `~/bin/uscis_case_status.py` | Self-contained `skills/case-status/scripts/uscis_case_status.py` (stdlib) |
| DesktopCommander / claude-flow | Native **Bash** + **GitHub MCP** (`mcp__github__*`) |

Unchanged: **Always Opus, medium thinking** (already the lean setting), silent routing,
the greeting (*"What do I do, boss?"*), and the legal carve-out (never present an
unverified legal answer as confirmed).

## Contents

- **`skills/batman`** — the router. Detects task type and routes silently across the
  remote surface. Start here.
- **`skills/doctor`** — remote health check. `doctor.sh` probes the self-contained core
  (legal skills, python3, native CLIs) and env creds, lists the retired desktop
  backends to confirm they're absent, and reminds you to verify the **live MCP**
  servers (which a script can't see). Exit code = number of RED core pieces.
- **Eight self-contained legal skills** — portable, zero-backend, work remotely as-is:
  `aos-audit`, `case-status`, `deadline-letter`, `form-checklist`, `intake-to-case`,
  `nta-review`, `priority-date`, `rfe-response`.

## Quick start

```bash
# health-check the remote surface first
bash skills/doctor/doctor.sh

# USCIS case status (Path A — needs firm API creds; else falls back to the public portal)
export USCIS_CLIENT_ID=... USCIS_CLIENT_SECRET=...
python3 skills/case-status/scripts/uscis_case_status.py EAC9999103402
```

Then invoke the router with your task and let it route. Legal/immigration work prefers
the dedicated `batman:*` skills; everything else routes to the matching MCP server or
native tool.

## Guardrails (unchanged from the firm's practice)

All eight legal skills are **internal work product, not legal advice**, and require the
firm's attorney sign-off before anything is filed, mailed, or sent. Client data is
confidential PII — keep it in the secure environment and never transmit over insecure
channels. Deadlines are computed with deterministic `datetime` math, never estimated.
