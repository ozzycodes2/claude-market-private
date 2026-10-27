# session-mgmt

Manage the lifecycle of a Claude Code working session — open one cleanly with
`start-session`, close it cleanly with `exit-session`.

- **`start-session <name>`** — begin a task in a fresh, isolated git worktree named
  after the argument. Uses the `EnterWorktree` tool (so the session's working directory
  follows into the worktree — no `cd` flood), places it under `.claude/worktrees/`,
  reports what untracked state the worktree inherited and whether it has a stack of its
  own, and if the name is a JIRA key (e.g. `ABC-123`) loads that story with the Atlassian
  CLI (`acli`) and summarizes the implementation ask. Then it stops and waits — it sets up
  the workspace, it doesn't start coding.
- **`exit-session`** — tear down the ephemeral resources a session spun up **permission-free**
  (in accept-edits mode — see [Permission mode](#permission-mode)), then quit the CLI, so you
  can wrap up with a single command and get a clean machine back.

## start-session

```
> /start-session ABC-123        # worktree "ABC-123", branch "worktree-ABC-123", + JIRA
> /start-session random-misc    # worktree "random-misc", branch "worktree-random-misc"
> start a worktree for PROJ-1505
```

Whatever name you pass becomes the worktree directory verbatim; `EnterWorktree` derives
the branch from it as `worktree-<name>`. The branch is based on a freshly-fetched origin
default (`worktree.baseRef: fresh`). JIRA loading is optional: a non-ticket name just
skips it, and if `acli` is missing or not authenticated (`acli auth login`) the worktree
is still created with a one-line note.

A new worktree is not empty of untracked state. `.worktreeinclude` at the repo root makes
Claude Code **copy** gitignored paths into it — `.env` among them — and
`worktree.symlinkDirectories` **symlinks** `node_modules` back to the main checkout. A
copied `.env` carries the source checkout's ports, `COMPOSE_PROJECT_NAME` and database URL
unchanged, so until a port-allocation recipe reassigns them the worktree's stack *is* the
main checkout's. The skill reports which files were copied and prints the command to fix
it, or says plainly when the repo has no per-worktree isolation at all.

Why `EnterWorktree` and not `git worktree add`? `EnterWorktree` switches the session
into the new worktree; `git worktree add` into a path does not, which forces a
`cd …/worktree &&` prefix onto every later command. This skill uses the tool on purpose.

## exit-session

```
> /exit-session
> clean up everything from this session
> tear down the stack and remove the worktree
> /exit-session worktree      # scope the sweep to one resource type
```

## What it cleans

| Resource | How | Safety |
|---|---|---|
| Background tasks / dev servers | `TaskStop`, `pkill -f`, `kill`; frees ports | permission-free |
| Docker / compose stacks | `just compose-down` / `docker compose down [-v]`; `docker rm -f` ad-hoc | permission-free (incl. `-v` volume wipe) |
| Subagent compose projects | `docker compose -p <worktree-basename> down -v --rmi local`, else removal by `com.docker.compose.project` label; `image prune -f` | permission-free; never `system`/`volume` prune |
| Local Tilt / Kubernetes | `just tilt-down` / `tilt down`; kills port-forwards (namespace kept) | permission-free |
| Scratch files | `rm` of `.claude/jobs/<id>/tmp` and this session's `/tmp/*` | permission-free |
| Git worktrees | `git worktree unlock` (session worktrees are locked) + `remove --force` + `prune` | permission-free |
| Subagent / orphan worktrees | same, for every `.claude/worktrees/agent-*` whose lock pid is yours, released, or dead; `rm -rf` for dirs `prune` leaves | permission-free; dirty non-session worktrees preserved |
| Merged local branches | `git branch -D` + `git fetch --prune` (session branches only, real `worktree-<name>` names) | permission-free; hand-named branches kept |
| Remote delete / resets / merge / force-push | handed back — still deny-listed | never silent |

## How it works

```
Phase 0   Permission mode       gate hook keeps the sweep out of auto / plan mode
Phase 0a  Own worktree          git rev-parse → is this session sitting in a worktree?
Phase 0b  Discover (read-only)  scripts/discover-resources.sh → full inventory
Phase 0c  Classify worktrees    lock pid → self / this session's agents / orphans / foreign
Phase 1   Stop runtime          background tasks, tilt down, compose down (+ agent projects)
Phase 2   Remove scratch        .claude/jobs/<id>/tmp + this session's /tmp/* paths
Phase 3   Git worktrees         3a own worktree, 3b /tmp checkouts, 3c subagents + orphans
Phase 4   Merged branches       git branch -D + fetch --prune (session branches)
Report    Summary, then exit    prints the summary, then `kill "$PPID"` quits the CLI
```

Two hard rules:

- **Scoped by live holder.** Tears down what *this* session created, including every
  worktree it handed to a subagent, plus worktrees whose holding `claude` pid is gone.
  Anything a *running* session still holds is listed as "left untouched," never removed —
  as is any non-session worktree carrying uncommitted changes.
- **Fully permission-free teardown — in accept-edits mode.** Teardown verbs are
  allow-listed, so the entire sweep runs without prompts — including
  `docker compose down -v` (volume/data wipe) and force-removing a worktree with
  uncommitted changes — and the CLI exits itself at the end. No mid-run confirmations. The
  only things it won't do are the still-denied remote/history ops
  (`git push origin --delete`, `git reset --hard`, `gh pr merge`, force-push), which are
  handed back.

## Discovery script

`scripts/discover-resources.sh [REPO_DIR] [--worktrees-only]` is a read-only inventory
(mutates nothing). It reports the session's own worktree, every other worktree classified
by lock holder, worktree directories git no longer tracks, current branch + PR/merge
status, listening ports and candidate session processes, Docker containers and the
volumes/networks/images grouped by compose project, Tilt sessions, scratch dirs, and
teardown-shaped `just` recipes. Missing tools are skipped with a note on stderr.
`--help` for usage.

`--worktrees-only` prints just the worktree sections. The full pass spends most of its
wall time in `pgrep -f` — roughly a second per pattern on a busy machine.

Each worktree gets one of six tags:

| Tag | Lock state | Disposition |
|---|---|---|
| `SELF` | the session is standing in it | Phase 3a |
| `THIS-SESSION` | lock pid is an ancestor of the script | Phase 3c |
| `STALE-UNLOCKED` | no lock — the agent finished and released it | Phase 3c |
| `FOREIGN-LIVE` | lock pid is a running `claude` | **left alone** |
| `ORPHAN-DEAD-PID` | lock pid no longer exists | Phase 3c |
| `ORPHAN-PID-RECYCLED` | pid alive but no longer `claude` (or `<defunct>`) | Phase 3c |

Attribution is mechanical in both halves: the lock reason git stores
(`claude agent <name> (pid N start <ts>)`) names the holding CLI process, and compose
derives its project name from the worktree directory basename, so a subagent's containers,
volumes, networks and locally built images all carry
`com.docker.compose.project=<basename>`.

## Permission mode

The sweep needs **accept-edits** mode (`default` and `bypassPermissions` also work). It does
**not** work in `auto` mode: entering `auto` strips every `Bash(...)` allow rule from
settings and routes each command through the auto-mode classifier instead, and destructive
teardown verbs are exactly what that classifier stops on — so an `auto`-mode sweep prompts
on `pkill`, on the scratch `rm`, on `docker compose down -v`, and on
`git worktree remove --force`. `plan` mode blocks the mutating tools outright.

`hooks/require-accept-edits.sh` (a `UserPromptSubmit` hook) therefore blocks
`/exit-session` in `auto` and `plan` mode and asks you to Shift+Tab into "accept edits on"
and re-run, rather than letting the sweep start and stall halfway through a half-torn-down
stack. The plugin can't flip the mode for you — no hook output field sets the permission
mode, and the `setMode` permission update is reachable only from the SDK permission bridge
— so the keystroke is the only lever.

## Permissions

For the sweep to run permission-free, the teardown verbs must be allow-listed in your
`settings.json` — `git worktree remove/prune`, `git branch -d/-D`, `git fetch --prune`,
`docker compose/stop/rm`, `pkill`, `kill`, `lsof`, `tilt down`, and scoped `rm -rf /tmp/*`.
`git branch -d/-D` is moved out of `deny` into `allow` so merged session branches can be
cleaned up automatically.

Still hard-denied (rewrite history or touch shared/remote state — **not** teardown):
`git push origin --delete`, `git reset --hard`, force-push to main, and `gh pr merge`. The
skill never attempts these; it surfaces the exact command for you. It also honors
`worktree.baseRef: fresh` when reasoning about branch bases.

## Self-exit

After teardown the skill prints its summary and then runs `kill "$PPID"` — the parent of the
Bash tool's shell is the `claude` CLI process, so this is the programmatic equivalent of
typing `/exit`. It only fires after a full sweep; a scoped sweep (e.g. `/exit-session worktree`)
stops at the summary and leaves you in the session.
