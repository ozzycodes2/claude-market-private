#!/usr/bin/env bash
# Bounce /exit-session back to the user when the session is in a permission mode the
# sweep cannot run in.
#
# Only plan mode qualifies: it blocks mutating tools outright, so there is no teardown
# to be had, and starting one would strand the user in a half-torn-down stack.
#
# auto mode used to be gated here too, on the grounds that entering it strips every Bash
# allow rule ("Ignoring dangerous permission <rule> from <source> (bypasses classifier)"
# in the debug log) and routes each command through the classifier. That gate fired on
# every single invocation and cost the user a Shift+Tab and a re-run each time. It is gone:
# the sweep is now described to the classifier in autoMode.allow, so auto mode passes the
# teardown verbs on their own merits rather than on an allow rule that is not there.
#
# Nothing in the plugin surface can change the mode: no hook output field sets it, and the
# setMode permission update is reachable only from the SDK permission bridge. So for plan
# mode the gate names the keystroke and stops.
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
  plan)
    reason="Not starting the teardown: this session is in plan mode, which blocks the mutating tools the sweep needs.

Press Shift+Tab until the footer reads \"accept edits on\", then re-run /exit-session."
    ;;
  *)
    exit 0
    ;;
esac

jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
