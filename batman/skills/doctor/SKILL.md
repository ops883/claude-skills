---
name: doctor
description: Use when Francisco asks to health-check batman, whether a route/tool/backend is working, why a route silently failed, or before relying on a token-saving or legal-authority layer — verifies the surface the REMOTE batman skill routes to (MCP servers + native tooling) and reports red/green
model: opus
---

# batman:doctor (remote profile)

Health check for the surface the **remote** batman skill routes to. The desktop
doctor probed local Mac repos; this one probes what a Claude Code cloud session
actually has — the self-contained skills, native tooling, env-var creds, and the
**MCP servers** that replace every retired local backend. It catches the two ways
remote batman silently rots: **routing to a retired desktop backend** that isn't
here, and **assuming an MCP server is connected** when the session never wired it up.
Either one drops batman into plain-model fallback while *looking* fully wired — which
for legal work means degraded answers presented as confident ones.

## How to run

```bash
bash "$(dirname "$0")/doctor.sh"   # from the skill dir
# or the plugin-relative path once installed:
bash "${CLAUDE_PLUGIN_ROOT:-.}/skills/doctor/doctor.sh"
```

The script is deterministic and dependency-free. Exit code = number of RED backends
in the self-contained core (0 = the always-on surface is healthy).

## Reading the report

- **GREEN** — ready now. Route there freely.
- **YELLOW** — present but needs the one-line step shown (e.g. set USCIS env creds).
  Treat the route as **unavailable** until it runs; tell Francisco the capability
  is offline rather than silently degrading.
- **RED** — a self-contained core piece is missing (a legal skill, python3, a core
  CLI). The always-on surface is broken; fix it before batman routes anywhere.

## The one thing the script can't see: live MCP

The script checks the container filesystem and env. It **cannot** see which MCP
servers are actually connected this session (that's a runtime socket, not a file).
After running it, cross-check the MCP section against the session's real tool
namespaces:

- Expected: **CourtListener** (legal authority), **GitHub** (code/PRs/CI),
  **Google Drive** (firm documents — replaces the old local firm-files path),
  **Gmail · Calendar · Docusign** (comms/scheduling/signing), **Context7 ·
  Playwright** (live docs / USCIS portal fallback).
- If a **legal** route needs CourtListener and it's absent this session, invoke the
  legal carve-out: say the authoritative source is unreachable and label anything
  from memory as unverified. Never present a degraded legal answer as confirmed.

## What "retired" means here

The script lists the desktop backends (`headroom`, RUFLO `/Users/tico/agents`,
`claude-for-legal`, `legal-sources`, `ai-lawyer`) and confirms they are **absent** —
which is the *expected, healthy* state remotely. If one is unexpectedly present, the
script flags YELLOW: this profile deliberately does not route to it, because the
MCP/native equivalent (CourtListener, Google Drive, native Bash/Grep, GitHub MCP)
covers the same capability without a local dependency.

## When to run it

- Before leaning on the token-saving/live-docs strategy or a legal-authority lookup
  for real work.
- Any time a route "did nothing" or an answer seems to have skipped a tool.
- At the start of any new remote session — it's the fastest way to confirm the whole
  batman surface (core + which MCP servers are live) in one shot.

## Fixing what it finds

For YELLOW, run the exact `fix:` shown, then re-run to confirm it flips GREEN. For a
missing MCP server, connect it in the session's MCP settings (or accept the degraded
route and, for legal work, apply the carve-out). An MCP server batman claims to route
to but that is never connected is a claim batman can't keep — connect it or drop the
route.
