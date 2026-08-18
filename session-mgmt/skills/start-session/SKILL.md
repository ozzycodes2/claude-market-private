---
name: start-session
description: >-
  Open a Claude Code working session in a fresh, isolated git worktree, so the
  user can start a task with a single /start-session <name>. Use at the START of a
  session when the user says "start session", "start a worktree", "spin up a
  worktree for COB-103", "begin work on <ticket>", "set up a workspace", or passes
  a name/ticket to work under. Creates and ENTERS a worktree via the EnterWorktree
  tool (never `git worktree add`) under .claude/worktrees/, named exactly after the
  argument, with a matching local branch. If the argument is a JIRA issue key (e.g.
  COB-103, SUBRO-1505), also loads that story from the Atlassian plugin when
  available and summarizes the implementation ask. Then stops and waits for the
  user's instructions — it sets up the workspace and context, it does not start
  implementing.
license: MIT
compatibility: >-
  Requires a git repo (EnterWorktree branches off a fresh origin default; honors
  worktree.baseRef: fresh). JIRA loading is optional and needs the Atlassian plugin
  (atlassian@machinify-plugins) enabled. EnterWorktree and the Atlassian MCP tools
  are deferred — load them via ToolSearch before calling.
metadata:
  argument-hint: "<worktree/branch name — a JIRA key like COB-103, or any slug like random-misc>"
---

# Start Session

Begin a working session inside a clean, isolated git worktree named after the task,
then load whatever context that task needs — and stop there. The point is a correct,
low-friction start: the worktree becomes the session's working directory so no `cd`
gymnastics follow, and if the task is a JIRA ticket its story is on screen before the
user types another word.

## Core principles

1. **EnterWorktree, never `git worktree add`.** EnterWorktree creates the worktree
   *and* switches the session's cwd into it. `git worktree add` into a path (especially
   `/tmp`) does not move the session cwd — Bash resets to the repo root after every
   call, forcing a `cd …/worktree &&` prefix on every command for the rest of the
   session. This skill exists to prevent that. Use the tool.
2. **The argument is the name — verbatim.** Whatever the user passes (`COB-103`,
   `random-misc`) is the worktree directory name *and* the local branch name. Do not
   rename, slugify, or prefix it. EnterWorktree names the branch after the worktree.
3. **Load context, don't act.** Create the worktree, load the story if there is one,
   report, then **stop and wait**. Do not read the codebase for an implementation plan,
   do not write code, do not enter plan mode — unless the user asks next.
4. **Degrade gracefully.** JIRA loading is a bonus, not a gate. If the argument isn't a
   ticket, or the Atlassian plugin isn't available, skip that step with a one-line note
   and still deliver the worktree.

## Workflow

### Phase 0 — Parse the argument (no tools)

- `NAME` = the argument, used verbatim. If none was given, ask the user for one (or a
  ticket) before doing anything — do not auto-generate a random name; the name carries
  meaning here.
- Validate `NAME` against EnterWorktree's rule: each `/`-separated segment may contain
  only letters, digits, dots, underscores, and dashes; ≤64 chars total. If it violates
  this, tell the user and stop.
- **Is it a JIRA key?** True if `NAME` matches `^[A-Za-z][A-Za-z0-9]*-[0-9]+$`
  (e.g. `COB-103`, `SUBRO-1505`). Uppercase it for the JIRA lookup only — the worktree
  and branch keep the exact string the user passed.

### Phase 1 — Preconditions (read-only)

- Confirm a git repo: `git rev-parse --git-dir`. (Outside a repo, EnterWorktree falls
  back to WorktreeCreate/WorktreeRemove hooks; if there are none, surface that and stop.)
- Confirm the session is **not already in a worktree**. EnterWorktree refuses to create
  a new worktree from inside one. If `git rev-parse --git-common-dir` shows this is
  already a linked worktree, tell the user (they likely want a fresh top-level session)
  and stop rather than nesting.

### Phase 2 — Create and enter the worktree

1. Load the deferred tool: `ToolSearch` with query `select:EnterWorktree`.
2. Call `EnterWorktree({ name: "<NAME>" })`. This creates `.claude/worktrees/<NAME>` on
   a new branch `<NAME>`, based on a freshly-fetched origin default branch
   (`worktree.baseRef: fresh`), and switches the session cwd into it.
3. Do **not** run `git worktree add`, `git checkout -b`, or any `cd`. The tool does all
   of it; the branch is created for you.

**Fallback (only if EnterWorktree is unavailable):** create the worktree at the
conventional path — `git worktree add .claude/worktrees/<NAME> -b <NAME> origin/<default>`
— then re-run `ToolSearch select:EnterWorktree` and call `EnterWorktree({ path:
".claude/worktrees/<NAME>" })` to enter it. If EnterWorktree truly cannot be loaded,
warn the user that the session cwd will not follow the worktree and that subsequent
commands must use absolute paths / `git -C <path>` (do not sprinkle `cd`).

### Phase 3 — Load the JIRA story (only if `NAME` is a ticket)

1. Load the deferred Atlassian tools: `ToolSearch` with query
   `select:mcp__plugin_atlassian_atlassian__getJiraIssue`. If nothing resolves, the
   plugin isn't available — note "Atlassian plugin not enabled; skipping story load"
   and go to Phase 4.
2. If `getJiraIssue` needs a `cloudId`, resolve it once via
   `getAccessibleAtlassianResources` (use the single/first site) — load it with
   `ToolSearch select:mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources`.
3. Call `getJiraIssue` with the uppercased issue key.
4. Read the issue and distill it — do not dump the raw payload. Summarize:
   - **Title / type / status** (one line).
   - **The implementation ask** — what the ticket wants built or changed, in your words.
   - **Acceptance criteria** if present, as a short checklist.
   - Notable links (design, parent epic, blocked-by) if any.
   If the fetch fails (permissions, unknown key), report the error in one line and
   continue — the worktree still stands.

### Phase 4 — Report and stop

Print a short summary and then wait:

- Worktree: `.claude/worktrees/<NAME>` · branch `<NAME>` · based on `origin/<default>`.
- If a ticket was loaded: the story summary and implementation ask from Phase 3.
- If not a ticket, or JIRA was skipped: say so in one line.
- End with an explicit handoff, e.g. *"Workspace ready. What would you like to build?"*

**Then stop.** Do not begin implementation, exploration, or planning until the user
gives the next instruction.

## Gotchas

- **EnterWorktree and the Atlassian tools are deferred.** Calling them without a prior
  `ToolSearch select:<name>` fails with InputValidationError. Always load first.
- **Already in a worktree → EnterWorktree refuses** a new `name`. Don't nest; surface it.
- **Name rules are strict.** Spaces, `@`, `:` and other punctuation are rejected. Fix
  with the user rather than silently mangling the name.
- **`baseRef: fresh` needs the remote.** The base is a freshly-fetched origin default;
  if offline or the remote is unreachable, EnterWorktree may fail — report it plainly.
- **Don't pre-create the branch.** EnterWorktree makes the branch; a prior
  `git checkout -b <NAME>` will collide with it.
- **JIRA is optional.** A non-ticket name (`random-misc`) is a perfectly valid session;
  just skip Phase 3.
