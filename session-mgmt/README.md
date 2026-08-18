# session-mgmt

Manage the lifecycle of a Claude Code working session — open one cleanly with
`start-session`, close it cleanly with `exit-session`.

- **`start-session <name>`** — begin a task in a fresh, isolated git worktree named
  after the argument, with a matching local branch. Uses the `EnterWorktree` tool (so
  the session's working directory follows into the worktree — no `cd` flood), places it
  under `.claude/worktrees/`, and if the name is a JIRA key (e.g. `COB-103`) loads that
  story from the Atlassian plugin and summarizes the implementation ask. Then it stops
  and waits — it sets up the workspace, it doesn't start coding.
- **`exit-session`** — tear down the ephemeral resources a session spun up, so you can
  wrap up with a single command and get a clean machine back.

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
| Background tasks / dev servers | `TaskStop`, `pkill -f`, `kill`; frees ports | auto (after plan) |
| Docker / compose stacks | `just compose-down` / `docker compose down`; `docker rm -f` ad-hoc | auto; `-v` (volume wipe) always asks |
| Local Tilt / Kubernetes | `just tilt-down` / `tilt down`; kills port-forwards (namespace kept) | auto (after plan) |
| Scratch files | `rm` of `.claude/jobs/<id>/tmp` and this session's `/tmp/*` | auto (after plan) |
| Git worktrees | `git worktree remove --force` + `git worktree prune` | auto (after plan) |
| Local branches | **printed for you to run** — `git branch -D` is deny-listed | never silent |
| Merges / resets / force-push | handed back — `gh pr merge`, `git reset --hard` deny-listed | never silent |

## How it works

```
Phase 0  Discover (read-only)   scripts/discover-resources.sh → full inventory
Phase 1  Stop runtime           background tasks, tilt down, docker compose down
Phase 2  Remove scratch         .claude/jobs/<id>/tmp + this session's /tmp/* paths
Phase 3  Git worktrees          worktree remove --force + prune
Phase 4  Destructive (gated)    print branch-delete / merge commands for the user
```

Two hard rules:

- **Session-scoped.** Only tears down what *this* session created. Other sessions'
  worktrees, branches, containers, and processes are listed as "left untouched," never removed.
- **Plan → confirm → execute.** Everything is discovered and shown as a risk-grouped plan
  before anything is stopped or deleted; volume wipes and any git-destructive op always ask first.

## Discovery script

`scripts/discover-resources.sh [REPO_DIR]` is a read-only inventory (mutates nothing). It
reports worktrees, current branch + PR/merge status, listening ports and candidate session
processes, Docker containers, Tilt sessions, scratch dirs, and teardown-shaped `just` recipes.
Missing tools are skipped with a note on stderr. `--help` for usage.

## Respects your settings

Reads the norms from your `settings.json`: `git branch -d/-D`, `git push origin --delete`,
`git reset --hard`, force-push to main, and `gh pr merge` are hard-denied — the skill never
attempts them, it surfaces the exact command for you. It also honors `worktree.baseRef: fresh`
when reasoning about branch bases.
