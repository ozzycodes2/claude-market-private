# session-mgmt

Manage the lifecycle of a Claude Code working session — open one cleanly with
`start-session`, close it cleanly with `exit-session`.

- **`start-session <name>`** — begin a task in a fresh, isolated git worktree named
  after the argument, with a matching local branch. Uses the `EnterWorktree` tool (so
  the session's working directory follows into the worktree — no `cd` flood), places it
  under `.claude/worktrees/`, and if the name is a JIRA key (e.g. `COB-103`) loads that
  story from the Atlassian plugin and summarizes the implementation ask. Then it stops
  and waits — it sets up the workspace, it doesn't start coding.
- **`exit-session`** — tear down the ephemeral resources a session spun up **permission-free**,
  then quit the CLI, so you can wrap up with a single command and get a clean machine back.

## start-session

```
> /start-session COB-103        # worktree + branch "COB-103", loads the JIRA story
> /start-session random-misc    # worktree + branch "random-misc", no ticket
> start a worktree for SUBRO-1505
```

Whatever name you pass becomes the worktree directory **and** the local branch,
verbatim. The branch is based on a freshly-fetched origin default (`worktree.baseRef:
fresh`). JIRA loading is optional: a non-ticket name just skips it, and if the Atlassian
plugin isn't enabled the worktree is still created with a one-line note.

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
| Local Tilt / Kubernetes | `just tilt-down` / `tilt down`; kills port-forwards (namespace kept) | permission-free |
| Scratch files | `rm` of `.claude/jobs/<id>/tmp` and this session's `/tmp/*` | permission-free |
| Git worktrees | `git worktree remove --force` + `git worktree prune` | permission-free |
| Merged local branches | `git branch -D` + `git fetch --prune` (session branches only) | permission-free |
| Remote delete / resets / merge / force-push | handed back — still deny-listed | never silent |

## How it works

```
Phase 0  Discover (read-only)   scripts/discover-resources.sh → full inventory
Phase 1  Stop runtime           background tasks, tilt down, docker compose down
Phase 2  Remove scratch         .claude/jobs/<id>/tmp + this session's /tmp/* paths
Phase 3  Git worktrees          worktree remove --force + prune
Phase 4  Merged branches        git branch -D + fetch --prune (session branches)
Report   Summary, then exit     prints the summary, then `kill "$PPID"` quits the CLI
```

Two hard rules:

- **Session-scoped.** Only tears down what *this* session created. Other sessions'
  worktrees, branches, containers, and processes are listed as "left untouched," never removed.
- **Fully permission-free teardown.** Teardown verbs are allow-listed, so the entire sweep
  runs without prompts — including `docker compose down -v` (volume/data wipe) and force-removing
  a worktree with uncommitted changes — and the CLI exits itself at the end. No mid-run
  confirmations. The only things it won't do are the still-denied remote/history ops
  (`git push origin --delete`, `git reset --hard`, `gh pr merge`, force-push), which are handed back.

## Discovery script

`scripts/discover-resources.sh [REPO_DIR]` is a read-only inventory (mutates nothing). It
reports worktrees, current branch + PR/merge status, listening ports and candidate session
processes, Docker containers, Tilt sessions, scratch dirs, and teardown-shaped `just` recipes.
Missing tools are skipped with a note on stderr. `--help` for usage.

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
