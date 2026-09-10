#!/usr/bin/env bash
# Bounce /exit-session back to the user when the session is in a permission mode the
# sweep cannot run in.
#
# exit-session's whole premise is that the teardown verbs (pkill, kill, rm -rf /tmp/*,
# docker compose, tilt down, git worktree remove) are allow-listed in settings.json, so
# the sweep runs start to finish without a prompt. Two modes break that premise:
#
#   auto  - strips every Bash allow rule at mode-entry time and routes each command
#           through the classifier instead ("Ignoring dangerous permission <rule> from
#           <source> (bypasses classifier)" in the debug log). Destructive teardown
#           verbs are exactly what the classifier stops on, so the sweep prompts on
#           nearly every step.
#   plan  - blocks mutating tools outright; there is no teardown to be had.
#
# Nothing in the plugin surface can change the mode: no hook output field sets it, and
# the setMode permission update is reachable only from the SDK permission bridge. So the
# gate blocks the prompt and names the keystroke instead of letting the sweep start and
# stall halfway through a half-torn-down stack.
set -euo pipefail

input=$(cat)

# This runs on every prompt in the session, so bail on the cheap substring test before
# spawning jq, and stay silent if jq is absent rather than warning once per prompt.
case "$input" in
  *exit-session*) ;;
  *) exit 0 ;;
esac
command -v jq >/dev/null || exit 0

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""' 2>/dev/null) || exit 0
mode=$(printf '%s' "$input" | jq -r '.permission_mode // ""' 2>/dev/null) || exit 0

# Matches /exit-session and the namespaced /session-mgmt:exit-session, with or without a
# scope argument. Anything else is somebody else's prompt.
if ! printf '%s' "$prompt" | grep -Eq '^[[:space:]]*/(session-mgmt:)?exit-session\b'; then
  exit 0
fi

case "$mode" in
  auto)
    reason="Not starting the teardown: this session is in auto mode, which strips the Bash allow rules exit-session depends on, so the sweep would prompt on nearly every step (pkill, rm, docker compose down -v, git worktree remove).

Press Shift+Tab until the footer reads \"accept edits on\", then re-run /exit-session."
    ;;
  plan)
    reason="Not starting the teardown: this session is in plan mode, which blocks the mutating tools the sweep needs.

Press Shift+Tab until the footer reads \"accept edits on\", then re-run /exit-session."
    ;;
  *)
    exit 0
    ;;
esac

jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
