#!/bin/bash
# PreToolUse hook template: hard-block a banned command shape, point at the
# allowed alternative. Copy to .claude/hooks/<rule-name>.sh and fill in the
# three CAPITALIZED placeholders below. See references/hook-patterns.md for
# the stdin/exit-code contract and BSD-grep portability notes.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# BANNED_PATTERN: extended regex for the disallowed invocation. Use
# [[:space:]] (not \s) and manual boundary classes (not \b) for BSD-grep
# (macOS default) compatibility. Example for "bare cargo fmt/clippy":
#   '(^|[^a-zA-Z0-9_])cargo([[:space:]]+\+[A-Za-z0-9_.-]+)?[[:space:]]+(fmt|clippy)([^a-zA-Z0-9_]|$)'
BANNED_PATTERN='REPLACE_ME'

if echo "$COMMAND" | grep -Eq "$BANNED_PATTERN"; then
  # ALLOWED_ALTERNATIVE: name the exact command(s) to use instead.
  echo "Blocked: REPLACE_ME_WITH_WHAT_WAS_BANNED. Use REPLACE_ME_WITH_ALLOWED_ALTERNATIVE instead." >&2
  exit 2
fi

exit 0
