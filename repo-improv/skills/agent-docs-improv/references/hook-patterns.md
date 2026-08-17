# PreToolUse hook patterns

## The contract

`.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/some-rule.sh" }
        ]
      }
    ]
  }
}
```

- `matcher` is the tool name (`Bash`, `Edit|Write|MultiEdit`, etc.) — pipe-separated
  for multiple tools.
- All hooks under one matcher share the array — append to `hooks`, don't add a
  second matcher block for the same tool.
- The script receives the full tool-call JSON on **stdin**. For `Bash`:
  `.tool_input.command`. For `Edit`/`Write`/`MultiEdit`: `.tool_input.file_path`.
- **Exit 0** — allow, no output needed.
- **Exit 2** — hard block. Anything written to **stderr** is shown to the
  agent as the reason (write a message that names the allowed alternative,
  not just "blocked").
- A softer "ask" outcome (used for content-based checks where you want a human
  glance rather than a static rule) is emitted as JSON on **stdout** instead of
  a bare exit code:
  ```bash
  jq -n --arg reason "Touches PHI-adjacent code — see docs/agents/phi-and-logging.md" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: $reason}}'
  exit 0
  ```
  Use `permissionDecision: "deny"` the same way for a soft block with a
  custom message instead of the plain exit-2 path.

## BSD grep portability

macOS ships BSD grep by default, not GNU grep. In `-E` (extended) mode it does
**not** support:
- `\s` (whitespace shorthand) — use `[[:space:]]` instead.
- `\b` (word boundary) — there's no equivalent class; build boundaries
  manually: `(^|[^a-zA-Z0-9_])pattern([^a-zA-Z0-9_]|$)`.

Test hook scripts on macOS specifically if that's the dev environment — a
regex that works under GNU grep in CI can silently no-op locally.

## Testing harness

Build the fake stdin JSON with `jq -n`, not string interpolation:

```bash
test_command() {
  jq -n --arg c "$1" '{tool_input: {command: $c}}' | ./.claude/hooks/some-rule.sh
  echo "exit=$?"
}

test_command 'cargo fmt'                 # expect exit=2 (blocked)
test_command 'just fmt'                  # expect exit=0 (allowed)
test_command 'cargo build'                # expect exit=0 (unrelated command)
```

String-interpolated JSON literals (`"{\"tool_input\":{\"command\":\"$1\"}}"`)
break silently on any embedded quote in the test command — `jq` fails to
parse, the script's own `jq -r` extraction comes back empty, and the
downstream `if` gate never fires, so a command that should have been blocked
reports a false "exit=0" pass. Always go through `jq -n --arg`.

## Dynamic-value edge case

When a hook validates the *value* of a flag (a PR title, a branch name), the
command may build that value dynamically instead of passing a literal string:

```
gh pr create --title "$(cat title.txt)" --body-file body.md
```

The extracted "title" here is the literal text `$(cat title.txt)`, not the
real runtime value — validating that string against the format regex will
always fail, producing a false-positive block on a command that might be
perfectly correct. Guard for this explicitly and let it through unjudged:

```bash
if echo "$VALUE" | grep -Eq '\$\(|`|\$\{|\$[A-Za-z_]'; then
  exit 0   # can't statically know the real value — don't guess
fi
```

A missed enforcement is recoverable (CI/the downstream check still catches a
malformed title); a false block on a legitimate dynamic command trains the
user to route around the hook entirely. Bias toward the former.

## Soft ("ask") pattern for content-based rules

Some rules aren't CLI-command-shaped — they're about *what's in a file*
(PHI-adjacent code paths, migration files, anything where the right call
needs human judgment, not a regex on a command string). For those, match on
`Edit|Write|MultiEdit` and case-match `.tool_input.file_path` against a
pattern, then emit the `ask` JSON above naming the relevant doc/rule instead
of trying to statically decide correctness. This is deliberately a nudge, not
a gate — Phase 2 of the parent skill explicitly excludes trying to hard-block
these with a `Bash` hook, since a `Bash` hook can't see file diffs at all.
