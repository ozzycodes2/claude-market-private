#!/usr/bin/env bash
# discover-resources.sh — read-only inventory of ephemeral resources that a
# Claude Code session may have created. Prints a sectioned report to stdout;
# diagnostics go to stderr. Mutates NOTHING.
#
# Usage:
#   discover-resources.sh [REPO_DIR] [--worktrees-only]
#   discover-resources.sh --help
#
# REPO_DIR defaults to the current working directory. Missing tools are skipped
# with a note on stderr rather than failing the whole run.
#
# --worktrees-only prints just the worktree sections and skips the process scan.
# The full pass spends most of its wall time in `pgrep -f`, which costs about a
# second per pattern on a busy machine; use this flag for `/exit-session
# worktree` and for re-checking the inventory after teardown.

set -uo pipefail

ARG=""
WT_ONLY=""
for a in "$@"; do
  case "$a" in
    -h|--help)        sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --worktrees-only) WT_ONLY=1 ;;
    *)                [[ -z "$ARG" ]] && ARG="$a" ;;
  esac
done
ARG="${ARG:-$PWD}"
have() { command -v "$1" >/dev/null 2>&1; }
section() { printf '\n=== %s ===\n' "$1"; }
note() { printf 'note: %s\n' "$1" >&2; }

# Resolve the argument to the MAIN checkout even when handed a linked worktree.
# Callers routinely pass their own worktree; the on-disk scans below look under
# $REPO/.claude/worktrees, which for a worktree is a nested path that cannot exist,
# so the whole inventory would come back empty.
REPO="$ARG"
SELF_WORKTREE=""
if have git && git -C "$ARG" rev-parse --git-dir >/dev/null 2>&1; then
  gitdir="$(cd "$ARG" && git rev-parse --absolute-git-dir 2>/dev/null)"
  commondir="$(cd "$ARG" && cd "$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || echo .)" && pwd)"
  if [[ -n "$commondir" && "$gitdir" != "$commondir" ]]; then
    SELF_WORKTREE="$(cd "$ARG" && git rev-parse --show-toplevel 2>/dev/null)"
    REPO="$(dirname "$commondir")"
  fi
fi

printf 'exit-session resource inventory\n'
printf 'repo: %s\n' "$REPO"

section "THIS SESSION'S OWN WORKTREE"
if [[ -n "$SELF_WORKTREE" ]]; then
  printf 'SELF_WORKTREE: %s\n' "$SELF_WORKTREE"
  printf 'branch:        %s\n' "$(git -C "$SELF_WORKTREE" branch --show-current 2>/dev/null)"
  printf 'main repo:     %s\n' "$REPO"
  printf 'ACTION: remove unconditionally in Phase 3a (ExitWorktree remove/discard_changes).\n'
else
  printf 'none — running from the main checkout; no self-worktree to tear down.\n'
fi

# --- Subagent / orphan worktrees -------------------------------------------
# Every worktree the CLI enters is locked with a reason naming the pid of the
# `claude` process that took it — including the ones `Agent(isolation:"worktree")`
# and bgIsolation create for subagents. That pid is an ancestor of this script,
# so it is a mechanical test for "mine" that survives context compaction.
ancestor_pids() {
  local p="$PPID" out=""
  while [[ -n "$p" && "$p" != "0" && "$p" != "1" ]]; do
    out="$out $p"
    p="$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')"
  done
  printf '%s' "$out"
}
ANCESTORS=" $(ancestor_pids) "

compose_resources() {
  # Compose derives its project name from the worktree directory basename, so
  # every container/volume/network/image a subagent's stack left behind is
  # labelled with it.
  local proj="$1" ids allflag
  have docker || return 0
  for kind in container volume network image; do
    # stopped containers still hold the label and still need removing
    allflag=""; [[ "$kind" == container ]] && allflag="-a"
    ids="$(docker "$kind" ls $allflag -q --filter "label=com.docker.compose.project=$proj" 2>/dev/null | tr '\n' ' ')"
    [[ -n "${ids// /}" ]] && printf '  docker %-9s %s\n' "$kind:" "$ids"
  done
  return 0
}

wt="" ; br="" ; lock=""
emit_worktree() {
  [[ "$wt" == "$REPO" ]] && return 0
  local base="${wt##*/}" pid="" cls="" dirty="" extra=""
  [[ "$lock" =~ \(pid\ ([0-9]+) ]] && pid="${BASH_REMATCH[1]}"

  if [[ -n "$SELF_WORKTREE" && "$wt" == "$SELF_WORKTREE" ]]; then
    cls="SELF"
  elif [[ -z "$lock" ]]; then
    cls="STALE-UNLOCKED"
  elif [[ -n "$pid" && "$ANCESTORS" == *" $pid "* ]]; then
    cls="THIS-SESSION"
  elif [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    # A live pid only means "another session" if it is still a claude process:
    # a recycled pid now belonging to something else, and a zombie whose comm
    # has gone empty, both pass `kill -0` while holding nothing. Reap those.
    # (The lock's `start` stamp is UTC while `ps -o lstart=` is local, so the
    # command name is the guard here, not the timestamp.)
    holder="$(ps -o comm= -p "$pid" 2>/dev/null | tr -d ' ')"
    extra="holder=${holder:-<none>}"
    # Compare the basename, not a substring: macOS prints the full executable
    # path, so a bare `*claude*` glob also matches an unrelated program sitting
    # in a directory with "claude" in its name. The allowlist covers the
    # runtimes the CLI reports as; anything else alive is not holding this lock.
    case "${holder##*/}" in
      claude|claude-*|node|bun) cls="FOREIGN-LIVE" ;;
      *)                        cls="ORPHAN-PID-RECYCLED" ;;
    esac
  else
    cls="ORPHAN-DEAD-PID"
  fi

  dirty="$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  printf '%-16s %s\n' "$cls" "$wt"
  printf '  branch=%s  uncommitted=%s  lockpid=%s %s\n' "${br:-<detached>}" "$dirty" "${pid:--}" "$extra"
  compose_resources "$base"
}

section "WORKTREES CLASSIFIED (self / subagents / orphans)"
printf 'ancestor pids (this session): %s\n' "${ANCESTORS# }"
printf 'SELF = Phase 3a | THIS-SESSION, STALE-UNLOCKED, ORPHAN-* = Phase 3c | FOREIGN-LIVE = leave\n'
printf 'uncommitted>0 on anything but THIS-SESSION/SELF = preserve and report (Phase 3c)\n\n'
if have git && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  while IFS= read -r line; do
    case "$line" in
      "worktree "*) wt="${line#worktree }" ;;
      "branch "*)   br="${line#branch refs/heads/}" ;;
      locked*)      lock="${line#locked}"; lock="${lock:-<no reason>}" ;;
      "")           [[ -n "$wt" ]] && emit_worktree; wt="" ; br="" ; lock="" ;;
    esac
  done < <(git -C "$REPO" worktree list --porcelain 2>/dev/null)
  [[ -n "$wt" ]] && emit_worktree
fi

section "UNREGISTERED WORKTREE DIRS (prune, then rm -rf)"
# git reports fully-resolved paths, so compare resolved against resolved: under
# /tmp (a symlink to /private/tmp on macOS) a plain string compare marks every
# live worktree as unregistered.
registered="$(git -C "$REPO" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p')"
for d in "$REPO/.claude/worktrees" "$REPO/.worktrees"; do
  [[ -d "$d" ]] || continue
  for p in "$d"/*; do
    [[ -d "$p" ]] || continue
    real="$(cd "$p" && pwd -P)"
    printf '%s\n' "$registered" | grep -qxF "$real" || printf '%s\n' "$p"
  done
done

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

if [[ -n "$WT_ONLY" ]]; then
  printf '\n=== END INVENTORY (worktrees only) ===\n'
  exit 0
fi

# --- Current branch + merge status ----------------------------------------
section "CURRENT BRANCH"
if have git && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  branch="$(git -C "$REPO" branch --show-current 2>/dev/null)"
  printf 'branch: %s\n' "${branch:-<detached>}"
  git -C "$REPO" status -s 2>/dev/null | head -30
  origin="$(git -C "$REPO" remote get-url origin 2>/dev/null)"
  # No origin means no PR to look up, and `gh --repo ""` blocks indefinitely
  # waiting on input rather than erroring out.
  if have gh && [[ -n "$branch" && -n "$origin" ]]; then
    GH_PROMPT_DISABLED=1 gh --repo "$origin" pr view "$branch" \
       --json number,state,mergedAt </dev/null 2>/dev/null \
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

section "DOCKER VOLUMES / NETWORKS / IMAGES BY COMPOSE PROJECT"
if have docker; then
  printf -- '--- compose projects present (project <- worktree dir basename) ---\n'
  { docker volume ls  --format '{{.Label "com.docker.compose.project"}}'
    docker network ls --format '{{.Label "com.docker.compose.project"}}'
    docker ps -a      --format '{{.Label "com.docker.compose.project"}}'
  } 2>/dev/null | grep -v '^$' | sort -u
  printf -- '--- anonymous volumes (unattributable: leave alone) ---\n'
  docker volume ls -q --filter label=com.docker.volume.anonymous 2>/dev/null | wc -l
  printf -- '--- dangling images ---\n'
  docker image ls -f dangling=true --format '{{.ID}} {{.Size}}' 2>/dev/null | head -20
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
