---
name: exit-session
description: >-
  Tear down the ephemeral resources a Claude Code working session created, then
  quit the CLI — so the user can wrap up with a single /exit-session. Use when the
  user says "exit session", "clean up this session", "tear down everything", "wrap
  up and clean up resources", "remove the worktree and scratch", "stop the
  background processes", "shut down the stack", or asks to clean up after finishing
  a task — even if they only name one resource (assume they want the full sweep
  unless they scope it). Runs teardown permission-free: stops background processes
  and dev servers, Docker/compose stacks, local Tilt/Kubernetes, git worktrees,
  merged local branches, and temp/scratch files without prompting, then exits the
  CLI. Strictly session-scoped — never touches resources belonging to other
  sessions, and still confirms before destroying data (volume wipes, uncommitted work).
license: MIT
compatibility: >-
  Assumes a git repo with optional worktrees under .claude/worktrees/ or /tmp;
  Docker + docker compose; optional Tilt (rancher-desktop/k3d); optional `just`
  task runner. Teardown verbs are allow-listed in settings.json so the sweep runs
  without prompts; the final self-exit uses `kill "$PPID"` (the CLI process).
argument-hint: "[optional: resource to scope to, e.g. worktree | docker | tilt | scratch]"
disable-model-invocation: true
---

# Exit Session

Teardown of everything a working session spun up: background processes, Docker/compose
stacks, local Tilt/Kubernetes, git worktrees, merged local branches, and scratch files —
leaving the machine as clean as before the session started — then quit the CLI. Designed
to run **permission-free**: the teardown verbs are allow-listed, so you execute the sweep
directly without stopping for confirmation, except for the two operations that destroy
*data* rather than just tear down ephemeral resources.

## Core principles

1. **Session-scoped, always.** Only tear down what *this* session created. Other
   sessions' worktrees, branches, containers, and background processes are off-limits —
   list them under "left untouched," never remove them. When you can't attribute a
   resource to this session, preserve it and say so.
2. **Discover, then execute — no plan-gate.** Do one read-only discovery pass to build
   the inventory, then tear down immediately. Teardown is pre-authorized; you do **not**
   pause for a "confirm the plan" step. Show the inventory as you go so progress is visible.
3. **Fully permission-free — no data-loss gate.** Every teardown of a resource this
   session created runs without a prompt, including `docker compose down -v` (wipes
   volumes / local DB state) and removing a worktree that still has **uncommitted** changes.
   The only thing you never do is run the still-denied remote/history ops (Phase 4) — those
   aren't teardown; hand them back.
4. **Preserve on doubt.** For anything you can't attribute to this session, default to
   leaving it and flagging it — a missed cleanup is cheap, a wrong deletion is not.
5. **No leading `cd`.** Use `git -C <path>` and absolute paths. A leading `cd` triggers a
   permission prompt (per the user's global CLAUDE.md) and defeats the point of a
   permission-free sweep.

## Workflow

Work the phases in order. Create a todo per phase so progress is visible.

### Phase 0 — Discover (read-only)

Build an inventory before touching anything. Run the bundled discovery script, which
gathers the whole picture in one read-only pass. Pass the repo root as an argument —
**do not `cd`**:

```
bash <skill-dir>/scripts/discover-resources.sh <repo-root>
```

(Substitute the real absolute path to this skill's `scripts/discover-resources.sh`, and
the absolute repo root.) It prints sections for worktrees, current branch + merge status,
background jobs/ports, Docker containers, Tilt/k8s, and scratch dirs. If the script is
unavailable, gather the same signals by hand (all read-only, all with `git -C`, no `cd`):

- **Background tasks this session spawned:** use the `TaskList` tool to enumerate live
  background shells and their `task_id`s. Cross-reference `ps` / `lsof -iTCP -sTCP:LISTEN -P -n`
  for dev servers (vite, `target/debug/api`, `cargo run -p api`, `npm run dev`, cloudflared,
  `kubectl port-forward`).
- **Worktrees:** `git -C <repo> worktree list` and `ls -la <repo>/.claude/worktrees/ 2>/dev/null`.
- **Branch:** `git -C <repo> branch --show-current`, `git -C <repo> status -s`, and whether
  its PR is merged (`gh pr view <branch> --json state,mergedAt`).
- **Docker:** `docker ps` (note session stacks like `postgres kafka localstack` and any
  ad-hoc `--name` containers).
- **Tilt/k8s:** `tilt get session 2>/dev/null`; `kubectl port-forward` procs.
- **Scratch:** `.claude/jobs/<id>/tmp` dirs and `/tmp/*` paths this session created (PR
  bodies, commit-msg files, review worktrees).

**Attribute each resource to this session or not.** Use the conversation history as the
source of truth for what this session started. Anything you didn't start goes in the
"left untouched" list. If the user passed a scope arg (e.g. `worktree`), limit the sweep
to that resource type.

### Phase 1 — Stop ephemeral runtime (permission-free)

1. **Background tasks:** call `TaskStop` for each `task_id` this session spawned. For
   manually-launched servers not tracked as tasks, `pkill -f '<pattern>'` or `kill <pid>`
   (use the narrowest pattern that matches only this session's process). Confirm ports are
   freed with `lsof -iTCP:<port> -sTCP:LISTEN -P -n`.
2. **Local Tilt/Kubernetes:** `just -f <repo>/justfile tilt-down` if the `justfile` defines
   it, else `tilt down`. Kill lingering `kubectl port-forward`. Leave the namespace in place.
3. **Docker:** `just -f <repo>/justfile compose-down` if defined, else
   `docker compose -f <repo>/<compose-file> down`. Add `-v` to also drop this session's
   volumes/local DB state — permission-free, no confirmation. `docker rm -f <cid>` for
   ad-hoc `--name` containers this session started.

### Phase 2 — Remove scratch files (permission-free)

Delete only paths this session created, using absolute paths:

- `rm -rf <repo>/.claude/jobs/<this-session-id>/tmp`
- `rm -f` the specific `/tmp/*` scratch files/dirs this session made (commit messages, PR
  bodies, review scratch).

Never blanket-wipe `/tmp` or `.claude/jobs/` — scope to this session's own paths.

### Phase 3 — Git worktrees (permission-free)

For each worktree **this session** created:

```
git -C <repo> worktree unlock <path>           # errors if not locked; that error is fine
git -C <repo> worktree remove --force <path>   # .claude/worktrees/<name> or /tmp/<name>
git -C <repo> worktree prune                    # clears stale admin refs (self-healing)
```

`git worktree remove --force` removes the worktree even if it has uncommitted changes —
that's intended here; run it without confirmation. **Unlock first.** A worktree the CLI
entered (`EnterWorktree`, or `claude -w`) is locked for the session, and the lock can
outlive the process that took it; without the unlock, removal fails with `cannot remove a
locked working tree, lock reason: claude session <name> (pid …)`. `remove -f -f` overrides
the lock too, if you prefer one command. If this session used the native
`ExitWorktree` tool to enter a worktree, prefer `ExitWorktree` with
`{"action":"remove","discard_changes":true}` so uncommitted work is discarded without a
prompt. Verify with `git -C <repo> worktree list`. Never remove a worktree tied to another
active session.

### Phase 4 — Merged local branches (permission-free) + destructive git (hand back)

**Merged local branches — delete directly.** `git branch -d/-D/--delete` is allow-listed
for teardown. For each local branch **this session** created whose PR is already merged (or
which is otherwise dead), delete it without prompting, using `git -C`:

```
git -C <repo> branch -D <branch>       # e.g. worktree branch left behind after merge
git -C <repo> fetch origin --prune     # clears the remote-tracking ref
```

Only delete branches you can attribute to this session and that are safe (merged, or never
pushed and clearly throwaway). If a branch has unmerged commits you can't attribute to
merged work, **preserve it** and list it under "left for you."

**Still hard-denied — never attempt, hand back to the user.** These remain deny-listed in
settings because they rewrite history or touch shared/remote state, and are **not**
teardown. Do not run them; print the exact command for the user:

- **Remote branch deletion:** `git push origin --delete <branch>` (shared remote).
- **History rewrite / merge / force-push:** `git reset --hard`, `gh pr merge`,
  `git push --force* origin main`.

If the wrap-up implies any of these, list the ready-to-paste command and stop there.

## Confirmation gating

- **Permission-free (run directly, no prompt — the whole sweep):** stopping tasks/servers,
  `tilt down`, `docker compose down` **including `-v`** (volume/data wipe), scratch `rm`,
  `git worktree remove --force` **including worktrees with uncommitted changes**,
  `git worktree prune`, `git branch -d/-D` for merged/throwaway session branches,
  `git fetch --prune`. No `AskUserQuestion` gate anywhere in teardown.
- **Never run — hand back:** `git push origin --delete`, `git reset --hard`, `gh pr merge`,
  force-push to main (still deny-listed).

## Gotchas (environment-specific — do not assume otherwise)

- **Teardown verbs are allow-listed**, so `git worktree remove/prune`, `git branch -d/-D`,
  `docker compose/stop/rm`, `pkill`, `kill`, `rm -rf /tmp/*`, and `tilt down` run without a
  prompt. `just -f <repo>/justfile compose-down` / `tilt-down` is the house convention —
  check the `justfile` before falling back to raw commands.
- **Still deny-listed:** `git push origin --delete`, `git reset --hard`, force-push to main,
  and `gh pr merge`. Attempting them wastes a turn on a guaranteed denial. Print-for-user is
  the only correct path.
- **`worktree.baseRef` is `fresh`** — worktrees branch from a freshly-fetched base, not local
  `main`. Don't assume a branch's base is local HEAD when reasoning about merge status.
- **Session worktrees are locked.** `git worktree remove --force` alone fails on them; run
  `git worktree unlock <path>` first (or `remove -f -f`). A stale lock naming a dead pid is
  still a lock.
- **The branch is `worktree-<name>`, not `<name>`.** EnterWorktree prefixes it, so deleting
  by the worktree directory name silently deletes nothing (or the wrong branch). Read the
  real name from `git -C <repo> worktree list --porcelain` before `branch -D`.
- **Removing a worktree removes its `.env` copy.** `.worktreeinclude` puts a real
  credential file in every worktree, so teardown is also the only thing that cleans those
  copies up — intended. Never extend that reasoning to the *main* checkout's `.env`.
- **`docker compose down -v` destroys volume data** (local Postgres/Kafka state) — that's the
  intended full teardown here; add `-v` without asking. Only this session's stack, never a
  shared one.
- **Scratch lives in `.claude/jobs/<8-char-id>/tmp`** and assorted `/tmp/*` paths. Only remove
  this session's own IDs.
- **Never treat another session's worktree/branch/container as yours** — preserve and report
  them as untouched.
- Use absolute paths and `git -C <path>`; never `cd` (per the user's global CLAUDE.md) — a
  leading `cd` reintroduces the permission prompt this skill is built to avoid.

## Final report, then exit

Close with a concise summary, print it, **then quit the CLI as the very last action**.

Print this summary first:

```
Session teardown complete.
  Stopped:   <background tasks / servers / ports freed>
  Docker:    <stacks / containers brought down>
  Tilt/k8s:  <tilt down; port-forwards killed> (namespace left in place)
  Scratch:   <paths removed>
  Worktrees: <paths removed + pruned>
  Branches:  <merged local branches deleted>
  Left for you (still denied): <git push origin --delete / reset --hard / gh pr merge, if any>
  Left untouched (other sessions): <worktrees/branches/containers preserved>

Exiting the CLI…
```

Then, as the **final tool call of the session**, quit Claude Code by terminating the CLI
process (its PID is the parent of the shell your Bash tool runs in):

```
kill "$PPID"
```

`$PPID` resolves to the `claude` process, so this is the programmatic equivalent of the
user typing `/exit`. Run it only after the teardown is done and the summary is printed —
nothing runs after it, because the CLI is gone. Do not run it if the user scoped the sweep
to a single resource and asked to stay in the session; in that case, stop after the summary.
