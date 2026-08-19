---
name: exit-session
description: >-
  Tear down the ephemeral resources a Claude Code working session created, so the
  user can wrap up with a single /exit-session. Use when the user says "exit
  session", "clean up this session", "tear down everything", "wrap up and clean
  up resources", "remove the worktree and scratch", "stop the background
  processes", "shut down the stack", or asks to clean up after finishing a task —
  even if they only name one resource (assume they want the full sweep unless they
  scope it). Detects and stops background processes and dev servers, Docker/compose
  stacks, local Tilt/Kubernetes, git worktrees, and temp/scratch files; surfaces
  (never silently deletes) local branches and any merge/reset/force operations for
  the user to confirm. Strictly session-scoped — never touches resources belonging
  to other sessions.
license: MIT
compatibility: >-
  Assumes a git repo with optional worktrees under .claude/worktrees/ or /tmp;
  Docker + docker compose; optional Tilt (rancher-desktop/k3d); optional `just`
  task runner. Respects the user's settings.json permission deny-list.
metadata:
  argument-hint: "[optional: resource to scope to, e.g. worktree | docker | tilt | scratch]"
disable-model-invocation: true
---

# Exit Session

Teardown of everything a working session spun up: background processes, Docker/compose
stacks, local Tilt/Kubernetes, git worktrees, and scratch files — leaving the machine
as clean as before the session started, without destroying anything the user still
needs.

## Core principles

1. **Session-scoped, always.** Only tear down what *this* session created. Other
   sessions' worktrees, branches, containers, and background processes are off-limits —
   list them under "left untouched," never remove them. When you can't attribute a
   resource to this session, preserve it and say so.
2. **Plan → confirm → execute.** Discover everything first (read-only), present a
   teardown plan grouped by risk, then execute. Never mutate before showing the plan.
3. **Respect the permission deny-list — don't fight it.** Branch deletion, `gh pr merge`,
   `git reset --hard`, and force-push to main are hard-denied in this user's settings and
   will fail. Do not attempt them. Surface the exact command for the user to run instead.
4. **Preserve on doubt.** For anything git-related or anything you're unsure about,
   default to leaving it and flagging it — a missed cleanup is cheap, a wrong deletion is not.

## Workflow

Work the phases in order. Create a todo per phase so progress is visible.

### Phase 0 — Discover (read-only, no confirmation)

Build an inventory before touching anything. Run the bundled discovery script from the
repo root, which gathers the whole picture in one read-only pass:

```
bash <skill-dir>/scripts/discover-resources.sh
```

(Substitute the real absolute path to this skill's `scripts/discover-resources.sh`.)
It prints sections for worktrees, current branch + merge status, background jobs/ports,
Docker containers, Tilt/k8s, and scratch dirs. If the script is unavailable, gather the
same signals by hand:

- **Background tasks this session spawned:** use the `TaskList` tool to enumerate live
  background shells and their `task_id`s. Cross-reference `ps` / `lsof -iTCP -sTCP:LISTEN -P -n`
  for dev servers (vite, `target/debug/api`, `cargo run -p api`, `npm run dev`, cloudflared,
  `kubectl port-forward`).
- **Worktrees:** `git worktree list` and `ls -la .claude/worktrees/ .worktrees/ 2>/dev/null`.
- **Branch:** `git branch --show-current`, `git status -s`, and whether its PR is merged
  (`gh pr status` / `gh pr view --json state,mergedAt`).
- **Docker:** `docker ps` (note session stacks like `postgres kafka localstack` and any
  ad-hoc `--name` containers).
- **Tilt/k8s:** `tilt get session 2>/dev/null` or check for a running Tiltfile; `kubectl port-forward` procs.
- **Scratch:** `.claude/jobs/<id>/tmp` dirs and `/tmp/*` paths this session created (PR
  bodies, commit-msg files, review worktrees).

**Attribute each resource to this session or not.** Use the conversation history as the
source of truth for what this session started. Anything you didn't start goes in the
"left untouched" list.

### Phase 1 — Stop ephemeral runtime (safe, auto after plan confirmed)

1. **Background tasks:** call `TaskStop` for each `task_id` this session spawned. For
   manually-launched servers not tracked as tasks, `pkill -f '<pattern>'` or `kill <pid>`
   (use the narrowest pattern that matches only this session's process). Confirm ports are
   freed with `lsof -iTCP:<port> -sTCP:LISTEN -P -n`.
2. **Local Tilt/Kubernetes:** `just tilt-down` if a `justfile` defines it, else `tilt down`.
   Kill lingering `kubectl port-forward`. Leave the namespace in place (intended).
3. **Docker:** `just compose-down` if defined, else `docker compose down`. Only add `-v`
   (wipes volumes/data) if the user explicitly asks — treat volume loss as destructive.
   `docker rm -f <cid>` for ad-hoc `--name` containers this session started.

### Phase 2 — Remove scratch files (safe, auto after plan confirmed)

Delete only paths this session created:

- `rm -rf .claude/jobs/<this-session-id>/tmp`
- `rm -f` the specific `/tmp/*` scratch files/dirs this session made (commit messages, PR
  bodies, review scratch).

Never blanket-wipe `/tmp` or `.claude/jobs/` — scope to this session's own paths.

### Phase 3 — Git worktrees (safe, auto after plan confirmed)

For each worktree **this session** created:

```
git worktree remove --force <path>     # e.g. .claude/worktrees/<name> or /tmp/<name>
git worktree prune                     # clears stale admin refs (self-healing)
```

If this session used the native `ExitWorktree` tool to enter a worktree, prefer
`ExitWorktree` with `{"action":"remove"}` (add `"discard_changes":true` only if the user
confirms discarding uncommitted work). Verify with `git worktree list`. Never remove a
worktree tied to another active session.

### Phase 4 — Destructive git ops (NEVER silent — hand to the user)

These are **deny-listed** in the user's settings and will fail if attempted. Do not run
them. Instead, print the exact commands and let the user execute:

- **Local branch deletion** (only for branches whose PR is already merged):
  `git branch -D <branch>`  — plus `git fetch origin --prune` (this one *is* allowed and
  clears the remote-tracking ref; you may run it).
- **Merges / resets / force-push:** never run `gh pr merge`, `git reset --hard`, or
  `git push --force* origin main`. If the wrap-up implies a merge, hand it back.

Present merged/orphaned branches as a list with the ready-to-paste `git branch -D` command
for each, and stop there.

## Confirmation gating

- **Auto after the plan is shown & confirmed:** stopping tasks/servers, `tilt down`,
  `docker compose down` (no `-v`), scratch `rm`, `git worktree remove`/`prune`.
- **Always ask first (AskUserQuestion), even mid-run:** `docker compose down -v`,
  discarding uncommitted worktree changes, anything under Phase 4.
- If the user invoked `/exit-session` with a scope arg (e.g. `worktree`), limit the sweep
  to that resource type; otherwise do the full sweep.

## Gotchas (environment-specific — do not assume otherwise)

- **`git branch -d/-D`, `git branch --delete`, `git push origin --delete`, `git reset --hard`,
  force-push to main, and `gh pr merge` are hard-denied.** Attempting them wastes a turn on a
  guaranteed denial. Print-for-user is the only correct path.
- **`worktree.baseRef` is `fresh`** — worktrees branch from a freshly-fetched base, not local
  `main`. Don't assume a branch's base is local HEAD when reasoning about merge status.
- **`docker stop`/`docker rm` and `git worktree remove/prune` are allow-listed** — they run
  without a prompt. Compose/Tilt teardown via `just compose-down` / `just tilt-down` is the
  house convention; check the `justfile` before falling back to raw commands.
- **`docker compose down -v` destroys volume data** (local Postgres/Kafka state). Never add
  `-v` unless the user explicitly asks to wipe data.
- **Scratch lives in `.claude/jobs/<8-char-id>/tmp`** and assorted `/tmp/*` paths. Only remove
  this session's own IDs.
- **Never treat another session's worktree/branch/container as yours.** The established norm is
  to preserve them and report them as untouched.
- Use absolute paths and `git -C <path>`; do not `cd` (per the user's global CLAUDE.md).

## Final report

Close with a concise summary in this shape:

```
Session teardown complete.
  Stopped:   <background tasks / servers / ports freed>
  Docker:    <stacks / containers brought down>
  Tilt/k8s:  <tilt down; port-forwards killed> (namespace left in place)
  Scratch:   <paths removed>
  Worktrees: <paths removed + pruned>
  Left for you (denied to me):
    git branch -D <branch>      # PR #N merged
  Left untouched (other sessions): <worktrees/branches/containers preserved>
```
