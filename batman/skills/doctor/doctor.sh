#!/usr/bin/env bash
# batman:doctor (remote profile) — health check for the surface the remote batman
# skill actually routes to. Deterministic, dependency-free. Reports GREEN / YELLOW /
# RED so batman never silently routes to a dead system.
#
#   GREEN  = ready to use now
#   YELLOW = present but needs a step (e.g. env var, connect the MCP server)
#   RED    = not available in this remote container
#
# Exit code = number of RED among the self-contained core (0 = the always-on surface
# is healthy). MCP/network backends are reported for information: this script checks
# the container filesystem and env; it CANNOT see live MCP sockets — those must be
# confirmed against the session's real tool namespaces (see the MCP section).

set -uo pipefail

red=0; yellow=0; green=0

if [ -t 1 ]; then G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; D=$'\e[2m'; B=$'\e[1m'; X=$'\e[0m'; else G=; Y=; R=; D=; B=; X=; fi

row() { # status label detail [fix]  — counts toward the summary/exit
  local s="$1" label="$2" detail="$3" fix="${4:-}"
  case "$s" in
    GREEN)  printf "  ${G}● GREEN ${X} %-24s %s\n" "$label" "$detail"; green=$((green+1));;
    YELLOW) printf "  ${Y}● YELLOW${X} %-24s %s\n" "$label" "$detail"; yellow=$((yellow+1))
            [ -n "$fix" ] && printf "             ${B}fix:${X} %s\n" "$fix";;
    RED)    printf "  ${R}● RED   ${X} %-24s %s\n" "$label" "$detail"; red=$((red+1))
            [ -n "$fix" ] && printf "             ${B}fix:${X} %s\n" "$fix";;
  esac
}

note() { # label detail  — informational, does NOT affect summary/exit
  printf "  ${D}○ %-24s %s${X}\n" "$1" "$2"
}

echo
echo "${B}batman:doctor — remote surface health$X"
echo "checking what a Claude Code remote session actually gives batman"
echo

echo "${B}Core (self-contained, must be GREEN — no backend needed)$X"
SKILLS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Count SKILL.md files whose immediate parent dir is a legal sub-skill —
# i.e. exclude the router ("batman") and this health-check ("doctor"). Matching on
# the parent-dir basename, not the full path, because the plugin dir is itself
# named "batman" and a path glob would wrongly exclude every skill under it.
subskills=0
while IFS= read -r f; do
  parent="$(basename "$(dirname "$f")")"
  case "$parent" in doctor|batman) ;; *) subskills=$((subskills+1));; esac
done < <(find "$SKILLS_DIR" -name SKILL.md 2>/dev/null)
if [ "$subskills" -ge 8 ]; then
  row GREEN "batman sub-skills" "$subskills self-contained legal skills present"
else
  row RED "batman sub-skills" "only $subskills of 8 legal skills found" "restore the missing skills/ dirs"
fi
if command -v python3 >/dev/null 2>&1; then
  row GREEN "python3 (date math)" "$(python3 --version 2>&1) — deterministic deadline/continuous-presence math ok"
else
  row RED "python3 (date math)" "python3 not on PATH" "install python3 (needed for deadline arithmetic)"
fi
for t in bash grep find; do
  command -v "$t" >/dev/null 2>&1 && row GREEN "native: $t" "on PATH" || row RED "native: $t" "missing" "unexpected in a remote container — check the image"
done

echo
echo "${B}Token-saving layer (remote strategy — no local headroom proxy)$X"
note "headroom (retired)" "desktop-only Rust proxy — NOT used remotely; compress with Read offset/limit + grep + persisted-output"
note "context7 (live docs)" "hosted MCP — verify it is connected in this session (see MCP section)"

echo
echo "${B}USCIS Case Status API (env-var creds; portal fallback always works)$X"
if [ -n "${USCIS_CLIENT_ID:-}" ] && [ -n "${USCIS_CLIENT_SECRET:-}" ]; then
  row GREEN "USCIS API creds" "USCIS_CLIENT_ID/SECRET set — Path A available"
else
  row YELLOW "USCIS API creds" "not set — Path A (official API) offline" "export USCIS_CLIENT_ID / USCIS_CLIENT_SECRET, or use the Playwright portal fallback"
fi
note "portal fallback" "egov.uscis.gov via Playwright MCP — works with no creds (confirm Playwright connected below)"

echo
echo "${B}Retired desktop backends (must NOT be present/routed to remotely)$X"
for pair in \
  "RUFLO agents:/Users/tico/agents" \
  "headroom:/Users/tico/Documents/GitHub/Dev-Tools/headroom" \
  "claude-for-legal:/Users/tico/Documents/GitHub/Legal/claude-for-legal" \
  "legal-sources:/Users/tico/Documents/GitHub/Legal/legal-sources" \
  "ai-lawyer:/Users/tico/ai-lawyer"; do
  label="${pair%%:*}"; dir="${pair#*:}"
  if [ -e "$dir" ]; then
    row YELLOW "$label" "unexpectedly present at $dir" "this is the remote profile — do not route here; use the MCP/native equivalent"
  else
    note "$label" "absent (expected) — covered by CourtListener MCP / native tools"
  fi
done

echo
echo "${B}MCP servers (verify LIVE in session — this script cannot see the socket)$X"
echo "  ${D}Cross-check these against the session's real tool namespaces:${X}"
echo "  ${D}  • CourtListener  — legal/immigration authority (search, read_document, citations)${X}"
echo "  ${D}  • GitHub         — code/PRs/CI/issues (mcp__github__*), the only remote git-forge path${X}"
echo "  ${D}  • Google Drive   — firm documents (replaces the local Law_Offices_Santiago path)${X}"
echo "  ${D}  • Gmail · Calendar · Docusign — firm comms / scheduling / e-signature${X}"
echo "  ${D}  • Context7 · Playwright — live docs / USCIS portal fallback${X}"
echo "  ${D}If a LEGAL route needs CourtListener and it is absent this session, invoke the${X}"
echo "  ${D}legal carve-out: say the authoritative source is unreachable and label anything${X}"
echo "  ${D}from memory as unverified. Never present a degraded legal answer as confirmed.${X}"

echo
echo "${B}Summary (self-contained core)$X"
printf "  ${G}%d green${X}  ${Y}%d yellow${X}  ${R}%d red${X}\n" "$green" "$yellow" "$red"
[ "$red" -gt 0 ]    && echo "  → RED: the always-on surface is broken — fix before batman routes anywhere."
[ "$yellow" -gt 0 ] && echo "  → YELLOW: works only after the one-line fix shown; treat as unavailable until then."
[ "$red" -eq 0 ] && [ "$yellow" -eq 0 ] && echo "  → Self-contained core healthy. Now confirm the MCP servers above are live in-session."
echo
exit "$red"
