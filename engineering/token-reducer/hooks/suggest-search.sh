#!/bin/bash
# Token Reducer — Suggest-Search Hook
# Fires on PostToolUse (Read) when a large file was just read in full.
# Zero output on small reads — only nudges when the read was big enough
# that an indexed search would likely have returned far fewer tokens.
#
# When installed via `/plugin install token-reducer@claude-code-skills` this
# hook is registered automatically from the plugin's hooks.json. No manual
# wiring required.
#
# If wiring it up manually, use ${CLAUDE_PLUGIN_ROOT} — a relative path like
# ./hooks/suggest-search.sh resolves against your current working directory,
# not the plugin root, and will silently fail in sessions started outside
# the plugin install dir.
#
#   .claude/settings.json:
#   {
#     "hooks": {
#       "PostToolUse": [{
#         "matcher": "Read",
#         "hooks": [{
#           "type": "command",
#           "command": "${CLAUDE_PLUGIN_ROOT}/hooks/suggest-search.sh"
#         }]
#       }]
#     }
#   }

OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"
THRESHOLD_CHARS=8000   # ~2,000 tokens

[ -z "$OUTPUT" ] && exit 0

LEN=${#OUTPUT}
[ "$LEN" -lt "$THRESHOLD_CHARS" ] && exit 0

cat << EOF
<token-reducer-tip>
That Read returned roughly $((LEN / 4)) tokens. If you were hunting for
something specific in this file (not reading it end-to-end on purpose), an
indexed search often returns far fewer tokens:
  /tr:search "<what you're looking for>"
(Run /tr:index once per project/session first to build the cache.)
</token-reducer-tip>
EOF
