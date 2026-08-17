#!/bin/bash
# PreToolUse hook template: validate the *value* of a flag on a specific
# subcommand against a required format (e.g. a PR title convention). Copy to
# .claude/hooks/<rule-name>.sh and fill in the CAPITALIZED placeholders. See
# references/hook-patterns.md for the dynamic-value skip logic explained
# below and the stdin/exit-code contract.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# TARGET_COMMAND_PATTERN: which invocation this rule even applies to.
# Example: gh pr create/edit — '(^|[^a-zA-Z0-9_])gh[[:space:]]+pr[[:space:]]+(create|edit)([^a-zA-Z0-9_]|$)'
if ! echo "$COMMAND" | grep -Eq 'REPLACE_ME_TARGET_COMMAND_PATTERN'; then
  exit 0
fi

# FLAG_NAMES: the long/short flag pair whose value this rule checks.
VALUE=$(echo "$COMMAND" | grep -oE -- '(--REPLACE_ME|-X)[[:space:]]+"[^"]*"' | head -1 | sed -E 's/^(--REPLACE_ME|-X)[[:space:]]+"//; s/"$//')
if [ -z "$VALUE" ]; then
  VALUE=$(echo "$COMMAND" | grep -oE -- "(--REPLACE_ME|-X)[[:space:]]+'[^']*'" | head -1 | sed -E "s/^(--REPLACE_ME|-X)[[:space:]]+'//; s/'\$//")
fi

# No statically-parseable literal value (built via heredoc, multi-line, etc.)
# — nothing to validate, let it through.
if [ -z "$VALUE" ]; then
  exit 0
fi

# Value contains shell substitution rather than a literal string — the real
# runtime value can't be known here, so don't guess. See hook-patterns.md.
if echo "$VALUE" | grep -Eq '\$\(|`|\$\{|\$[A-Za-z_]'; then
  exit 0
fi

# REQUIRED_FORMAT_PATTERN: the format this value must match.
if echo "$VALUE" | grep -Eq 'REPLACE_ME_REQUIRED_FORMAT_PATTERN'; then
  exit 0
fi

echo "Blocked: \"$VALUE\" doesn't match REPLACE_ME_FORMAT_DESCRIPTION." >&2
exit 2
