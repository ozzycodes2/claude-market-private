---
name: exit-session
description: >-
  Tear down the ephemeral resources a Claude Code working session created, then
  quit the CLI — so the user can wrap up with a single /exit-session. Use when the
  user says "exit session", "clean up this session", "tear down everything", "wrap
  up and clean up resources", "remove the worktree and scratch", "stop the
  background processes", "shut down the stack", "clean up the agent worktrees", or asks
  to clean up after finishing a task — even if they only name one resource (assume they
  want the full sweep unless they scope it). Runs teardown permission-free: stops
  background processes and dev servers, Docker/compose stacks plus their volumes,
  networks and images, local Tilt/Kubernetes, git worktrees, merged local branches, and
  temp/scratch files without prompting, then exits the CLI. Covers the worktrees and
  Docker resources left behind by subagents spawned during the session, not just the
  primary agent's own worktree — both determined from git locks and Docker labels rather
  than from recall. Never touches resources a still-live session holds.
license: MIT
compatibility: >-
  Assumes a git repo with optional worktrees under .claude/worktrees/ or /tmp;
  Docker + docker compose; optional Tilt (rancher-desktop/k3d); optional `just`
  task runner. Runs without prompts in default, accept-edits and bypassPermissions
  mode via allow rules in settings.json, and in `auto` mode — which strips those rules
  — via an autoMode.allow entry describing the sweep. Only plan mode is refused, by the
  bundled UserPromptSubmit hook, since it blocks mutating tools outright. The final
  self-exit uses `kill "$PPID"` (the CLI process).
argument-hint: "[optional: resource to scope to, e.g. worktree | docker | tilt | scratch]"
disable-model-invocation: true
---

# Exit Session

Teardown of everything a working session spun up: background processes, Docker/compose
stacks with their volumes, networks and locally built images, local Tilt/Kubernetes, git
worktrees — the session's own **and every one it handed to a subagent** — merged local
branches, and scratch files, leaving the machine as clean as before the session started,
then quit the CLI. Designed
to run **permission-free**: the teardown verbs are allow-listed in default, accept-edits
and bypassPermissions mode, and described to the classifier in `autoMode.allow` for `auto`
mode, so you execute the sweep directly without stopping for confirmation — including the
two operations that destroy *data* rather than just tear down ephemeral resources. Only
plan mode is refused (Phase 0).

## Core principles

1. **Scoped by live holder, not by memory.** A resource is off-limits when a *live*
   session still holds it — not merely because you don't recall creating it. Worktrees
   locked by another running `claude` pid, and their containers, are preserved and listed
   under "left untouched." Everything with no live holder — this session's own worktrees,
   its subagents' worktrees, and worktrees whose holder pid is gone — is in scope.
2. **Attribute mechanically first, from memory second.** Three resources are *knowable
   with certainty*, so ask the system, never your recollection:
   - the worktree this session sits in → `git rev-parse` (Phase 0a);
   - which worktrees belong to this session's subagents → the git **lock reason**, which
     names the holding `claude` pid; that pid is an ancestor of your own shell (Phase 0c);
   - which Docker resources belong to a given worktree → the
     `com.docker.compose.project` label, which equals the worktree directory basename.

   Conversation history is the fallback for genuinely ambiguous resources (an ad-hoc
   `docker run --name`, a scratch path), never the primary test for a worktree. By the
   time a real session reaches teardown its context has usually compacted, so the
   `EnterWorktree` and `Agent(isolation:"worktree")` calls are long gone — and "I don't
   remember creating it" then silently becomes "it must be someone else's," which is how
   a session leaks its own worktree, and every worktree it gave a subagent, on every run.
3. **Discover, then execute — no plan-gate.** Do one read-only discovery pass to build
   the inventory, then tear down immediately. Teardown is pre-authorized; you do **not**
   pause for a "confirm the plan" step. Show the inventory as you go so progress is visible.
4. **Fully permission-free — no data-loss gate.** Once Phase 0 settles the mode, every
   teardown of a resource this session created runs without a prompt, including
   `docker compose down -v` (wipes volumes / local DB state) and removing a worktree that
   still has **uncommitted** changes. The only thing you never do is run the still-denied
   remote/history ops (Phase 4) — those aren't teardown; hand them back.
5. **Preserve on doubt — except where git already answered.** For anything you can't
   attribute, default to leaving it and flagging it: a missed cleanup is cheap, a wrong
   deletion is not. This does **not** apply to the worktrees Phase 0a and 0c settle
   mechanically — those are answered by `git rev-parse` and the lock pid, so there is no
   doubt to preserve on, and skipping them is the failure mode this rule is blamed for.
   The one live remnant of the rule: a worktree with **uncommitted changes** that is not
   this session's own gets preserved and reported, never discarded (Phase 3c).
6. **No leading `cd`.** Use `git -C <path>` and absolute paths. A leading `cd` triggers a
   permission prompt (per the user's global CLAUDE.md) and defeats the point of a
   permission-free sweep.
7. **One plain command per Bash call while in a worktree.** When the session is inside a
   linked worktree — the normal case for this sweep — Claude Code's isolation validator
   refuses any Bash line it cannot statically prove stays inside it: *"too complex to
   verify that it stays inside the worktree; break it into plain, separate commands."*
   It rejects `;` and `&&` chains, `$(…)` substitution, and heredocs **even when every
   component is read-only**. It is a static-analysis gate, not a permission check, so no
   allow rule and no permission mode gets past it. Issue separate Bash calls, in parallel
   in one message where they're independent. The one exception is the bundled discovery
   script: it is a single `bash <script>` call, and the commands inside its own subshell
   are not re-examined — which is also why it is the cheapest way to run discovery.

## Workflow

Work the phases in order. Create a todo per phase so progress is visible.

### Phase 0 — Permission mode (preflight)

**If you are reading this, the mode is already fine.** The bundled `UserPromptSubmit`
hook (`hooks/require-accept-edits.sh`) blocks `/exit-session` in plan mode before you ever
see the prompt, and it let this invocation through. Proceed straight to Phase 0a.

Only plan mode is refused, because it blocks the mutating tools the sweep needs. Every
other mode works, by two different routes: `default`, `acceptEdits` and
`bypassPermissions` honour the `Bash(...)` allow rules in settings.json, while `auto`
strips them all at mode-entry (`Ignoring dangerous permission <rule> from <source>
(bypasses classifier)` in the debug log) and relies instead on the `autoMode.allow` entry
describing this sweep. Do not reintroduce an auto-mode gate: it fired on every single
invocation and cost the user a Shift+Tab and a re-run each time.

Nothing here can flip the mode for the user, so do not try: no hook output field sets it
(`PreToolUse` returns only `permissionDecision` / `permissionDecisionReason` /
`updatedInput` / `additionalContext`), and the `setMode` permission update is reachable
only from the SDK permission bridge. The keystroke is the only lever. If prompts start
landing on verbs that should be covered, stop the sweep, report what has already been
torn down, and say which rule is missing — do not grind through the sweep one
confirmation at a time.

### Phase 0a — Identify this session's own worktree (read-only, deterministic)

**Do this first, before the discovery script.** It is three read-only commands and it
settles the question the rest of the sweep keeps getting wrong: *is the directory I am
sitting in a worktree that should be torn down?*

Three separate Bash calls, issued in parallel in one message — not `&&`-joined, and not
wrapped in `echo "$(…)"` (Principle 7):

```
git -C <cwd> rev-parse --git-dir           # linked worktree -> <main>/.git/worktrees/<name>
git -C <cwd> rev-parse --git-common-dir    # linked worktree -> <main>/.git   (differs!)
git -C <cwd> rev-parse --show-toplevel     # linked worktree -> the worktree path itself
```

`git rev-parse --git-dir --git-common-dir --show-toplevel` in one call is also fine —
that is a single command with three flags, not a chain.

- **`--git-dir` and `--git-common-dir` differ** → the session is inside a **linked
  worktree**. `--show-toplevel` is `SELF_WORKTREE`, and the parent of `--git-common-dir`
  is `MAIN_REPO`. `SELF_WORKTREE` is a teardown target **unconditionally** — do not ask
  whether you remember creating it. A session lands in a worktree because it was put
  there (`/start-session`, `EnterWorktree`, `claude -w`), so by construction it is this
  session's. Read the real branch from `git -C <MAIN_REPO> worktree list --porcelain`
  (it is `worktree-<name>`, not `<name>`).
- **They are the same** → the session is in the main checkout. There is no self-worktree,
  and Phase 3a is a no-op. This says **nothing** about the other worktrees in the list:
  a session running from the main checkout still owns every worktree it handed to a
  subagent. Phase 0c classifies those; do not conclude they are all other sessions'.

`MAIN_REPO` — not `SELF_WORKTREE` — is the `<repo-root>` argument for everything that
follows. The bundled script resolves this itself and prints a `THIS SESSION'S OWN WORKTREE`
section, but pass `MAIN_REPO` anyway: handing a worktree path to a hand-rolled scan makes
it look at `<worktree>/.claude/worktrees`, a nested path that cannot exist, so the on-disk
worktree section comes back empty and the sweep silently has nothing to do.

### Phase 0b — Discover (read-only)

Build an inventory before touching anything. Run the bundled discovery script, which
gathers the whole picture in one read-only pass. Pass the repo root as an argument —
**do not `cd`**:

```
bash <skill-dir>/scripts/discover-resources.sh <repo-root>
```

Add `--worktrees-only` when you only need the worktree picture — for
`/exit-session worktree`, or to re-check the inventory after Phase 3. The full pass spends
most of its wall time in `pgrep -f`, about a second per pattern on a busy machine.

(Substitute the real absolute path to this skill's `scripts/discover-resources.sh`, and
the absolute repo root.) Write it exactly that way: `bash ` then the bare unquoted path.
Quoting the path, or executing the script directly without `bash `, changes the command
string enough to miss the allow rule and costs a prompt. It prints sections for the
self-worktree, **every worktree classified by lock holder** (Phase 0c), unregistered
worktree directories, current branch + merge status, background jobs/ports, Docker
containers, Docker volumes/networks/images grouped by compose project, Tilt/k8s, and
scratch dirs. If the script is unavailable, gather the same signals by hand (all
read-only, all with `git -C`, no `cd`):

- **Background tasks this session spawned:** use the `Monitor` tool to enumerate live
  background shells and their `task_id`s — it is deferred, so `ToolSearch select:Monitor`
  first. (There is no `TaskList` tool; asking for one wastes a turn.) Cross-reference
  `ps` / `pgrep -f` / `lsof -iTCP -sTCP:LISTEN -P -n` for dev servers (vite,
  `target/debug/api`, `cargo run -p api`, `npm run dev`, cloudflared,
  `kubectl port-forward`).
- **Worktrees:** `git -C <repo> worktree list --porcelain` (the `--porcelain` form is what
  carries the lock reasons Phase 0c needs) and
  `ls -la <repo>/.claude/worktrees/ 2>/dev/null`.
- **Branch:** `git -C <repo> branch --show-current`, `git -C <repo> status -s`, and whether
  its PR is merged (`gh pr view <branch> --json state,mergedAt`).
- **Docker:** `docker ps -a` (note session stacks like `postgres kafka localstack` and any
  ad-hoc `--name` containers), plus `docker volume ls`, `docker network ls`, and
  `docker image ls` — each with
  `--filter label=com.docker.compose.project=<worktree-basename>` to attribute them.
- **Tilt/k8s:** `tilt get session 2>/dev/null`; `kubectl port-forward` procs.
- **Scratch:** `.claude/jobs/<id>/tmp` dirs and `/tmp/*` paths this session created (PR
  bodies, commit-msg files, review worktrees).

**Attribute each resource mechanically where you can, from history only where you can't.**
`SELF_WORKTREE` (Phase 0a) is yours, and no amount of not remembering it changes that.
Every other worktree is settled by its lock holder (Phase 0c), and each worktree's Docker
resources by its compose-project label. Conversation history is the source of truth only
for what those two keys cannot reach: ad-hoc `docker run --name` containers, ports, and
scratch paths. Anything you didn't start and can't attribute goes in "left untouched."
If the user passed a scope arg (e.g. `worktree`), limit the sweep to that resource type.

A compacted or `/clear`ed context is the normal case here, not an edge case. When history
is thin, that is a reason to lean harder on the mechanical answers — never a reason to
downgrade `SELF_WORKTREE` or a subagent worktree to "probably another session's."

### Phase 0c — Classify every other worktree by its lock holder (read-only)

Phase 0a settles only the worktree you are *standing in*. Subagents get their own:
`Agent(isolation:"worktree")` and the `worktree.bgIsolation` setting both put each
subagent in `<MAIN_REPO>/.claude/worktrees/agent-<17-hex>` on a `worktree-agent-<id>`
branch. A session that fanned out across a dozen agents therefore owns a dozen worktrees
it never entered — and because nothing in conversation history survives compaction, they
are the bulk of what this sweep used to leak.

The classifier is the **lock reason**. Every worktree the CLI enters is locked as
`claude agent <name> (pid <PID> start <ts>)`, and that PID is the `claude` process — an
**ancestor of your own shell**. So:

| Lock state | Meaning | Disposition |
|---|---|---|
| pid is one of your ancestors | this session's subagent | tear down (3c) |
| **no lock** | the agent finished and released it | tear down (3c) |
| pid alive **and** is a `claude` process | another live session | **leave**, report |
| pid gone, or recycled into a non-`claude` process | crashed session's orphan | tear down (3c) |

The bundled discovery script does this classification for you and prints one line per
worktree under `WORKTREES CLASSIFIED`, tagged `SELF` / `THIS-SESSION` /
`STALE-UNLOCKED` / `FOREIGN-LIVE` / `ORPHAN-DEAD-PID` / `ORPHAN-PID-RECYCLED`, with the
branch, the uncommitted-file count, and each worktree's Docker resources. Read the tags
and act on them; do not re-derive the attribution by hand.

Doing it by hand takes one command plus one liveness check per distinct pid:

```
git -C <MAIN_REPO> worktree list --porcelain     # 'locked claude agent … (pid N start …)'
ps -o comm= -p <N>                               # basename not claude -> orphan
```

Your own ancestor pids come from walking `ps -o ppid= -p <pid>` up from `$PPID`.

Compare the **basename** of what `ps` prints. On macOS it is the full executable path, so
testing for `claude` anywhere in the string also matches an unrelated program living under
a directory with `claude` in its name — and that reads a dead lock as a live session,
preserving the worktree forever.

**Do not use the `start` timestamp to confirm a pid.** The lock records it in UTC while
`ps -o lstart=` prints local time, so they disagree by your UTC offset on a perfectly
healthy lock. The command name is the recycling guard.

Also check `ListAgents` for subagents of *this* session still running. If any are, their
worktrees are in use: skip them, finish the rest of the sweep, and name them in the
report rather than reaping a worktree out from under a working agent.

### Phase 1 — Stop ephemeral runtime (permission-free)

1. **Background tasks:** call `TaskStop` (deferred — `ToolSearch select:TaskStop`) for
   each `task_id` this session spawned. For
   manually-launched servers not tracked as tasks, `pkill -f '<pattern>'` or `kill <pid>`
   (use the narrowest pattern that matches only this session's process). Confirm ports are
   freed with `lsof -iTCP:<port> -sTCP:LISTEN -P -n`.
2. **Local Tilt/Kubernetes:** `just -f <repo>/justfile tilt-down` if the `justfile` defines
   it, else `tilt down`. Kill lingering `kubectl port-forward`. Leave the namespace in place.
3. **Docker:** `just -f <repo>/justfile compose-down` if defined, else
   `docker compose -f <repo>/<compose-file> down`. Add `-v` to also drop this session's
   volumes/local DB state — permission-free, no confirmation. `docker rm -f <cid>` for
   ad-hoc `--name` containers this session started.
4. **Docker left by subagent stacks.** A subagent that ran compose inside its own worktree
   created a *separate* project, named after that worktree's directory — so
   `compose down` in the main checkout does not touch it, and its containers, volumes and
   networks outlive the agent. For each worktree Phase 0c marked as in-scope, tear down
   its project by label (`<proj>` = the worktree directory basename):

   ```
   docker compose -p <proj> down -v --remove-orphans --rmi local
   ```

   `--rmi local` drops the images that project built itself and leaves pulled base images
   (`postgres:16`, `apache/kafka`, `localstack`) alone. If the project's compose file is
   gone with the worktree, `compose -p` has nothing to read; remove by label instead, one
   plain command per call:

   ```
   docker rm -f $(docker ps -aq --filter label=com.docker.compose.project=<proj>)
   docker volume rm $(docker volume ls -q --filter label=com.docker.compose.project=<proj>)
   docker network rm $(docker network ls -q --filter label=com.docker.compose.project=<proj>)
   docker image rm $(docker image ls -q --filter label=com.docker.compose.project=<proj>)
   ```

   Then `docker image prune -f` for untagged layers. **Never** `docker system prune`,
   `image prune -a`, or `volume prune`: those reach shared base images, the build cache,
   and anonymous volumes that carry no project label and no owner — `volume prune` in
   particular would destroy another session's database. Anonymous volumes
   (`com.docker.volume.anonymous`) are unattributable; `compose down -v` removes the ones
   bound to the project's own containers, and the rest stay.

### Phase 2 — Remove scratch files (permission-free)

Delete only paths this session created, using absolute paths:

- `rm -rf <repo>/.claude/jobs/<this-session-id>/tmp`
- `rm -f` the specific `/tmp/*` scratch files/dirs this session made (commit messages, PR
  bodies, review scratch).

Never blanket-wipe `/tmp` or `.claude/jobs/` — scope to this session's own paths.

### Phase 3 — Git worktrees (permission-free)

Three kinds of worktree get torn down here. 3a is the one the session is standing in; 3c
is the larger pile the session handed to its subagents, and the one this phase used to
walk past.

**3a. `SELF_WORKTREE` — the worktree this session is in (from Phase 0a).** Remove it
unconditionally. You are inside it, so use the native tool, which relocates the session
back to `MAIN_REPO` as it goes:

```
ExitWorktree({"action":"remove","discard_changes":true})
```

`discard_changes: true` is correct and deliberate: uncommitted work in a session worktree
is teardown scope, not a data-loss gate to stop on (Principle 4). If `ExitWorktree` is
unavailable, fall back to the `git` sequence below run against `MAIN_REPO`. If it refuses,
report what it said — do not leave the worktree standing silently.

**3b. Any other worktree this session created** — throwaway checkouts under `/tmp`,
review clones, a second worktree spun up mid-task:

Three separate Bash calls, in this order — `;`-joining them gets the whole line refused
under worktree isolation (Principle 7):

```
git -C <MAIN_REPO> worktree unlock <path>           # errors if not locked; that error is fine
git -C <MAIN_REPO> worktree remove --force <path>   # .claude/worktrees/<name> or /tmp/<name>
git -C <MAIN_REPO> worktree prune                   # clears stale admin refs (self-healing)
```

`git worktree remove --force` removes the worktree even if it has uncommitted changes —
that's intended here; run it without confirmation. **Unlock first.** A worktree the CLI
entered (`EnterWorktree`, or `claude -w`) is locked for the session, and the lock can
outlive the process that took it; without the unlock, removal fails with `cannot remove a
locked working tree, lock reason: claude session <name> (pid …)`. `remove -f -f` overrides
the lock too, if you prefer one command.

**3c. Subagent and orphan worktrees (from Phase 0c).** Every worktree tagged
`THIS-SESSION`, `STALE-UNLOCKED`, `ORPHAN-DEAD-PID`, or `ORPHAN-PID-RECYCLED` gets removed
here. `FOREIGN-LIVE` ones do not — a running `claude` process is using them.

Per worktree, in this order, one plain command per Bash call:

```
git -C <MAIN_REPO> worktree unlock <path>
git -C <MAIN_REPO> worktree remove --force <path>
```

Then, once for the whole batch:

```
git -C <MAIN_REPO> worktree prune
rm -rf <unregistered-worktree-dir>     # dirs prune leaves behind (script lists them)
```

Branches, after the worktrees are gone:

- `worktree-agent-<id>` and `worktree-<name>` are **auto-generated throwaway** names.
  Delete them: `git -C <MAIN_REPO> branch -D worktree-agent-<id>`.
- A worktree on a **hand-named** branch (`worker-lib-split`, `fix-rustls-advisories`) holds
  deliberate work. Remove the worktree, **keep the branch**, and list it in the report. The
  commits survive the worktree; deleting the branch is what loses them.

**The one preserve rule left.** A worktree whose uncommitted-file count is non-zero and
that is *not* `SELF` or `THIS-SESSION` — i.e. another session's leftover, live or dead —
is preserved, not forced. Its dirty files were never committed anywhere, so `remove
--force` is the only irreversible step in this whole sweep. Report the path and the file
count and move on. For `SELF` and `THIS-SESSION`, dirty is still teardown scope
(Principle 4): force them.

Verify with `git -C <MAIN_REPO> worktree list` and confirm `SELF_WORKTREE` and every
in-scope agent worktree are gone from it. A run that ends with the session's own worktree —
or a pile of `agent-*` entries it spawned — still listed has failed this phase, even if
every other line of the report is green. Never remove a worktree tied to another active
session.

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

- **Permission-free in every mode the hook admits (run directly, no prompt — the whole sweep):**
  stopping tasks/servers, `tilt down`, `docker compose down` **including `-v`**
  (volume/data wipe), scratch `rm`,
  `git worktree remove --force` **including worktrees with uncommitted changes**,
  `git worktree prune`, `git branch -d/-D` for merged/throwaway session branches,
  `git fetch --prune`, `docker compose -p <proj> down -v --rmi local` and the
  label-filtered `docker rm` / `volume rm` / `network rm` / `image rm` for a subagent's
  project, `docker image prune -f`. No `AskUserQuestion` gate anywhere in teardown.
- **Never run — hand back:** `git push origin --delete`, `git reset --hard`, `gh pr merge`,
  force-push to main (still deny-listed).
- **Never run at all — not even on request here:** `docker system prune`,
  `docker image prune -a`, `docker volume prune`, `docker builder prune`. They are
  unscoped: they reach base images, the build cache, and label-less anonymous volumes
  belonging to sessions and projects this sweep has no claim on. Label-filtered removal is
  the only correct path.

## Gotchas (environment-specific — do not assume otherwise)

- **Teardown verbs are allow-listed**, so `git worktree remove/prune`, `git branch -d/-D`,
  `docker compose/stop/rm/ps`, `pkill`, `kill`, `pgrep`, `ps`, `lsof`, `rm -rf /tmp/*`,
  and `tilt down/get` run without a prompt. `just -f <repo>/justfile compose-down` /
  `tilt-down` is the house convention — check the `justfile` before falling back to raw
  commands.
- **Bash allow rules match the raw command string**, with `*` spanning `/` and spaces —
  they are not gitignore-style path globs (that matcher serves `Read`/`Edit` rules only).
  So `Bash(rm -rf *.claude/jobs/*)` does cover an absolute scratch path. It does not cover
  flag reorderings like `rm -fr` or `rm -r -f`; keep to `rm -rf`.
- **`auto` mode has no allow rules**, so in that mode the thing clearing the sweep is the
  `autoMode.allow` entry describing it, not the `Bash(...)` rules — those are stripped at
  mode entry. The practical difference: a classifier judgement is probabilistic where an
  allow rule is not. If a teardown verb does get stopped in `auto`, that is a gap in the
  prose entry; report it rather than retrying the command.
- **Still deny-listed:** `git push origin --delete`, `git reset --hard`, force-push to main,
  and `gh pr merge`. Attempting them wastes a turn on a guaranteed denial. Print-for-user is
  the only correct path.
- **`worktree.baseRef` is `fresh`** — worktrees branch from a freshly-fetched base, not local
  `main`. Don't assume a branch's base is local HEAD when reasoning about merge status.
- **A compacted context is not evidence of innocence.** The `EnterWorktree` and
  `Agent(isolation:"worktree")` calls are usually gone from context by teardown time — long
  sessions compact repeatedly. Reasoning "I see no worktree creation in my history, so this
  worktree must be another session's" is the single most common way this skill leaves
  worktrees behind. Phases 0a and 0c exist precisely so this judgement is never made from
  memory.
- **Subagents get worktrees you never entered.** `Agent(isolation:"worktree")` and the
  `worktree.bgIsolation: "worktree"` setting create `.claude/worktrees/agent-<17-hex>` per
  agent, on a `worktree-agent-<id>` branch. A session that fanned out ten agents owns ten
  worktrees that never appear in `ExitWorktree`'s view and that `SELF_WORKTREE` reasoning
  never reaches — tens of gigabytes across a week. They are Phase 3c's job, and the lock
  pid, not your memory, is what identifies them.
- **The worktree lock reason names the holding pid**, as
  `claude agent <name> (pid N start <ts>)`. `N` is the `claude` CLI process and an ancestor
  of your own shell when the agent was yours. Do **not** compare the lock's `start` stamp
  with `ps -o lstart=`: the lock is UTC, `ps` is local, so they disagree by your offset on
  a perfectly healthy lock.
- **Check the holder's *basename*, not a substring.** macOS `ps -o comm=` prints the full
  executable path, so matching `*claude*` also matches an unrelated program under a
  directory with `claude` in its name — and reads a dead lock as a live session. A zombie
  reports `<defunct>` on macOS and nothing on Linux while still passing `kill -0`; both
  mean the holder is gone.
- **An unlocked `.claude/worktrees/*` entry means the agent finished and released it** —
  that is the signal this skill was missing, not a reason for caution. Agents under
  `bgIsolation` release the lock when they complete.
- **Compose project name == worktree directory basename.** That is why a subagent's stack
  survives `compose down` run from the main checkout: it is a different project. It is also
  why attribution is exact — `com.docker.compose.project=<basename>` on every container,
  volume, network, and locally built image. Networks named `<basename>_default` left in
  `docker network ls` are the visible symptom.
- **`--rmi local` vs `--rmi all`.** `local` drops only images the project built itself;
  `all` would delete `postgres:16` and friends out from under every other project on the
  machine. Use `local`.
- **Give the discovery script `MAIN_REPO`, never the worktree.** Its on-disk scan looks at
  `<arg>/.claude/worktrees`. Pass a worktree path and that becomes
  `<worktree>/.claude/worktrees` — nonexistent — so the section is empty and the sweep
  concludes there is nothing to remove.
- **Session worktrees are locked.** `git worktree remove --force` alone fails on them; run
  `git worktree unlock <path>` first (or `remove -f -f`). A stale lock naming a dead pid is
  still a lock.
- **`worktree prune` leaves the directory.** It clears the admin ref, not the files on
  disk, so a crashed session leaves a full checkout under `.claude/worktrees/<name>` that
  no longer appears in `worktree list`. The discovery script lists these under
  `UNREGISTERED WORKTREE DIRS`; they need `rm -rf`, not another `prune`.
- **The branch is `worktree-<name>`, not `<name>`.** EnterWorktree prefixes it, so deleting
  by the worktree directory name silently deletes nothing (or the wrong branch). Read the
  real name from `git -C <repo> worktree list --porcelain` before `branch -D`.
- **An agent's branch is not always auto-named.** A subagent that renamed its branch sits in
  `agent-<hex>` on something like `fix-rustls-advisories`. The *directory* is still
  throwaway; the *branch* is not. Delete only `worktree-*`-prefixed branches; keep the rest
  and report them.
- **Removing a worktree removes its `.env` copy.** `.worktreeinclude` puts a real
  credential file in every worktree, so teardown is also the only thing that cleans those
  copies up — intended. Never extend that reasoning to the *main* checkout's `.env`.
- **`docker compose down -v` destroys volume data** (local Postgres/Kafka state) — that's the
  intended full teardown here; add `-v` without asking. Only this session's stack, never a
  shared one.
- **Scratch lives in `.claude/jobs/<8-char-id>/tmp`** and assorted `/tmp/*` paths. Only remove
  this session's own IDs.
- **Never treat a *live* session's worktree/branch/container as yours** — preserve and
  report those as untouched. A worktree whose holder pid is gone is not a live session's;
  it is debris, and reaping it is this phase's job.
- Use absolute paths and `git -C <path>`; never `cd` (per the user's global CLAUDE.md) — a
  leading `cd` reintroduces the permission prompt this skill is built to avoid.

## Final report, then exit

Close with a concise summary, print it, **then quit the CLI as the very last action**.

Print this summary first:

```
Session teardown complete.
  Stopped:   <background tasks / servers / ports freed>
  Docker:    <stacks / containers brought down>
  Docker (subagent projects): <projects down -v; volumes/networks/images removed, by count>
  Tilt/k8s:  <tilt down; port-forwards killed> (namespace left in place)
  Scratch:   <paths removed>
  Worktree:  <SELF_WORKTREE removed — this session's own> (or: none; ran from the main checkout)
  Subagent worktrees: <N removed: this session's agents + released/orphaned> (or: none found)
  Orphan dirs: <unregistered .claude/worktrees dirs rm -rf'd>
  Branches:  <worktree-* branches deleted; hand-named branches kept>
  Left for you (still denied): <git push origin --delete / reset --hard / gh pr merge, if any>
  Left untouched (live sessions): <FOREIGN-LIVE worktrees + their containers, with holder pid>
  Left untouched (dirty, not ours): <path — N uncommitted files>

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
