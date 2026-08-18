#!/usr/bin/env bash
# discover-resources.sh — read-only inventory of ephemeral resources that a
# Claude Code session may have created. Prints a sectioned report to stdout;
# diagnostics go to stderr. Mutates NOTHING.
#
# Usage:
#   discover-resources.sh [REPO_DIR]
#   discover-resources.sh --help
#
# REPO_DIR defaults to the current working directory. Missing tools are skipped
# with a note on stderr rather than failing the whole run.

set -uo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

REPO="${1:-$PWD}"
have() { command -v "$1" >/dev/null 2>&1; }
section() { printf '\n=== %s ===\n' "$1"; }
note() { printf 'note: %s\n' "$1" >&2; }

printf 'exit-session resource inventory\n'
printf 'repo: %s\n' "$REPO"

# --- Git worktrees ---------------------------------------------------------
section "GIT WORKTREES"
if have git && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$REPO" worktree list 2>/dev/null || note "git worktree list failed"
  printf -- '--- worktree dirs on disk ---\n'
  for d in "$REPO/.claude/worktrees" "$REPO/.worktrees"; do
    [[ -d "$d" ]] && ls -1 "$d" 2>/dev/null | sed "s|^|$d/|"
  done
  # only DIRECTORIES under /tmp look like throwaway worktrees; skip stray log files.
  # Use shell globbing (follows the /tmp -> /private/tmp symlink; `find /tmp` would not).
  shopt -s nullglob
  for p in /tmp/*wt* /tmp/vc-* /tmp/co-wt-*; do [[ -d "$p" ]] && printf '%s\n' "$p"; done
  shopt -u nullglob
else
  note "not a git repo (or git missing): $REPO"
fi

# --- Current branch + merge status ----------------------------------------
section "CURRENT BRANCH"
if have git && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  branch="$(git -C "$REPO" branch --show-current 2>/dev/null)"
  printf 'branch: %s\n' "${branch:-<detached>}"
  git -C "$REPO" status -s 2>/dev/null | head -30
  if have gh && [[ -n "$branch" ]]; then
    gh --repo "$(git -C "$REPO" remote get-url origin 2>/dev/null)" pr view "$branch" \
       --json number,state,mergedAt 2>/dev/null \
       || note "no PR found for branch $branch (or gh unavailable)"
  fi
fi

# --- Background processes / listening ports --------------------------------
section "LISTENING PORTS (dev servers, port-forwards)"
if have lsof; then
  lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null \
    | grep -Ei 'node|vite|cargo|target/debug|api|worker|cloudflared|kubectl|just|python' \
    || note "no matching listeners"
else
  note "lsof unavailable"
fi
section "CANDIDATE SESSION PROCESSES"
if have pgrep; then
  for pat in vite 'target/debug' 'cargo run' 'npm run dev' cloudflared 'kubectl port-forward'; do
    pids="$(pgrep -f "$pat" 2>/dev/null | tr '\n' ' ')"
    [[ -n "$pids" ]] && printf '%-24s %s\n' "$pat" "$pids"
  done
else
  note "pgrep unavailable"
fi

# --- Docker ----------------------------------------------------------------
section "DOCKER CONTAINERS"
if have docker; then
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null \
    || note "docker ps failed (daemon down?)"
else
  note "docker unavailable"
fi

# --- Tilt / local k8s ------------------------------------------------------
section "TILT / LOCAL K8S"
if have tilt; then
  tilt get session 2>/dev/null | head -5 || note "no active tilt session"
else
  note "tilt unavailable"
fi
[[ -f "$REPO/Tiltfile" ]] && printf 'Tiltfile present at %s/Tiltfile\n' "$REPO"

# --- Scratch dirs ----------------------------------------------------------
section "SCRATCH (.claude/jobs, /tmp)"
if [[ -d "$REPO/.claude/jobs" ]]; then
  find "$REPO/.claude/jobs" -maxdepth 2 -type d -name tmp 2>/dev/null
else
  note "no .claude/jobs dir"
fi
ls -1d /tmp/*commit* /tmp/*pr-* /tmp/*review* /tmp/rfc-* /tmp/*-work 2>/dev/null \
  || note "no obvious /tmp scratch matched"

# --- just recipes (house teardown wrappers) --------------------------------
section "JUST TEARDOWN RECIPES"
if have just && [[ -f "$REPO/justfile" || -f "$REPO/Justfile" ]]; then
  just --justfile "$REPO/justfile" --list 2>/dev/null \
    | grep -Ei 'down|stop|clean|teardown|tilt' || note "no teardown-shaped recipes"
else
  note "no justfile / just unavailable"
fi

printf '\n=== END INVENTORY ===\n'
