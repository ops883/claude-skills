#!/bin/bash
# SessionStart hook — standardizes a fresh Claude Code (web/remote) session.
#
# 1. Installs the repo's dev dependencies (pytest) so the tests/ suite runs.
# 2. Verifies the batman plugin is present on disk (it ships in this repo, so a
#    fresh clone already has it — no manual /plugin install needed).
# 3. Runs batman:doctor to report which self-contained backends are healthy and
#    reminds you to confirm the live MCP servers. Its output becomes session
#    context, so every session starts health-checked.
#
# Idempotent and non-interactive. Never aborts the session: always exits 0.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT" || exit 0

echo "-- session-start: standardizing environment --"

# 1. Dev dependencies (pytest). Cached into the container after first run.
if [ -f requirements-dev.txt ]; then
  echo "* installing dev dependencies (requirements-dev.txt)..."
  python3 -m pip install --quiet --disable-pip-version-check -r requirements-dev.txt \
    && echo "  ok: dev deps ready" \
    || echo "  WARN: dev dep install failed (tests may not run)"
fi

# 2/3. Batman standardization + health check.
DOCTOR="$ROOT/batman/skills/doctor/doctor.sh"
if [ -f "$DOCTOR" ]; then
  echo "* batman plugin present -- running batman:doctor..."
  bash "$DOCTOR" || true   # doctor's exit code = RED count; never abort the session
else
  echo "WARN: batman plugin not found at batman/ -- skill is not standardized in this clone"
fi

echo "-- session-start: done --"
exit 0
