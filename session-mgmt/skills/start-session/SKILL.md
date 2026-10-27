---
name: start-session
description: >-
  Open a Claude Code working session in a fresh, isolated git worktree, so the
  user can start a task with a single /start-session <name>. Use at the START of a
  session when the user says "start session", "start a worktree", "spin up a
  worktree for ABC-123", "begin work on <ticket>", or passes a name/ticket to work
  under. Creates and ENTERS a worktree via the EnterWorktree tool (never `git
  worktree add`) under .claude/worktrees/, named exactly after the argument, on a
  local branch `worktree-<argument>`. Reports what the worktree inherited
  (`.worktreeinclude` copies, symlinked node_modules) and whether its `.env` still
  points at the main checkout's stack. If the argument is a JIRA key (e.g.
  ABC-123, PROJ-1505), also loads that story with the Atlassian CLI (`acli`) when
  available and summarizes the implementation ask. Also renames the session to the
  argument (the same effect as `/rename <NAME>`) so it's easy to find in `/resume`.
  Then stops and waits — it sets up the workspace and context, it does not implement.
license: MIT
compatibility: >-
  Requires a git repo (EnterWorktree branches off a fresh origin default; honors
  worktree.baseRef: fresh). JIRA loading is optional and needs the Atlassian CLI
  (`acli`) installed and authenticated (`acli auth login`). EnterWorktree is
  deferred — load it via ToolSearch before calling.
argument-hint: "<worktree/branch name — a JIRA key like ABC-123, or any slug like random-misc>"
disable-model-invocation: true
---

# Start Session

Begin a working session inside a clean, isolated git worktree named after the task,
then load whatever context that task needs — and stop there. Point is a correct,
low-friction start: worktree becomes the session's working directory so no `cd`
gymnastics follow, and if the task is a JIRA ticket its story is on screen before the
user types another word.

## Core principles

1. **EnterWorktree, never `git worktree add`.** EnterWorktree creates the worktree
   *and* switches the session's cwd into it. `git worktree add` into a path (especially
   `/tmp`) does not move the session cwd — Bash resets to repo root after every
   call, forcing a `cd …/worktree &&` prefix on every command for rest of the
   session. This skill exists to prevent that. Use the tool.
2. **The argument is the name — verbatim.** Whatever the user passes (`ABC-123`,
   `random-misc`) is the worktree directory name. Do not rename, slugify, or prefix it.
   EnterWorktree derives the branch as `worktree-<NAME>` — that prefix is the tool's, not
   yours to add or strip. Report the branch it actually created; do not claim `<NAME>`.
3. **Load context, don't act.** Create the worktree, load the story if there is one,
   report, then **stop and wait**. Do not read the codebase for an implementation plan,
   do not write code, do not enter plan mode — unless the user asks next.
4. **Degrade gracefully.** JIRA loading is a bonus, not a gate. If the argument isn't a
   ticket, or `acli` is missing or unauthenticated, skip that step with a one-line note
   and still deliver the worktree.
5. **Rename the session to `NAME`.** `/rename` is a user-typed command with no callable
   tool. What actually makes a name show up in `/resume` is a `custom-title` record
   appended to the session's own transcript JSONL file — not the `name` field of
   `~/.claude/sessions/<pid>.json`. That pid file only drives the live "concurrent
   sessions" indicator while the process runs, and is deleted the instant the process
   exits, so writing it alone renames nothing durable. Write the transcript record
   directly (see Phase 2.5); mirror into the pid file too, best-effort, for the live
   indicator.
6. **One plain command per Bash call, from Phase 2 onward.** The moment EnterWorktree
   returns, the session is worktree-isolated, and Claude Code's isolation validator
   refuses any Bash line it cannot statically prove stays inside the worktree:
   *"too complex to verify that it stays inside the worktree; break it into plain,
   separate commands."* It rejects `;` and `&&` chains, `$(…)` substitution, and
   heredocs — **even when every component is read-only**, and even for a bare
   `acli jira workitem view`. No permission rule can pre-empt it. So after Phase 2,
   never join commands: issue them as separate Bash calls, in parallel in a single
   message where they're independent. That costs no extra turns; a refusal costs
   several.
7. **Execute silently; report once.** Don't narrate phase transitions, tool calls, or
   intermediate checks ("Preconditions pass...", "Now Phase 2.5...", "Verifying...").
   Run Phases 0-3 without commentary. The only output is the Phase 4 report — unless a
   real precondition fails and needs a user decision (that's a stop, not narration).

## Workflow

### Phase 0 — Parse the argument (no tools)

- `NAME` = the argument, used verbatim. If none given, ask the user for one (or a
  ticket) before doing anything — do not auto-generate a random name; the name carries
  meaning here.
- Validate `NAME` against EnterWorktree's rule: each `/`-separated segment may contain
  only letters, digits, dots, underscores, and dashes; ≤64 chars total. If it violates
  this, tell the user and stop.
- **Is it a JIRA key?** True if `NAME` matches `^[A-Za-z][A-Za-z0-9]*-[0-9]+$`
  (e.g. `ABC-123`, `PROJ-1505`). Uppercase it for the JIRA lookup only — the worktree
  and branch keep the exact string the user passed.

### Phase 1 — Preconditions (read-only)

- Confirm a git repo: `git rev-parse --git-dir`. (Outside a repo, EnterWorktree falls
  back to WorktreeCreate/WorktreeRemove hooks; if none, surface that and stop.)
- Confirm the session is **not already in a worktree**. EnterWorktree refuses to create
  a new worktree from inside one. If `git rev-parse --git-common-dir` shows this is
  already a linked worktree, tell the user (they likely want a fresh top-level session)
  and stop rather than nesting.

### Phase 2 — Create and enter the worktree

1. Load the deferred tool: `ToolSearch` with query `select:EnterWorktree`.
2. Call `EnterWorktree({ name: "<NAME>" })`. This creates `.claude/worktrees/<NAME>` on
   a new branch `worktree-<NAME>`, based on a freshly-fetched origin default branch
   (`worktree.baseRef: fresh`), and switches the session cwd into it.
3. Do **not** run `git worktree add`, `git checkout -b`, or any `cd`. The tool does all
   of it; the branch is created for you.

**Fallback (only if EnterWorktree unavailable):** create the worktree at the
conventional path — `git worktree add .claude/worktrees/<NAME> -b worktree-<NAME> origin/<default>`
— then re-run `ToolSearch select:EnterWorktree` and call `EnterWorktree({ path:
".claude/worktrees/<NAME>" })` to enter it. If EnterWorktree truly cannot be loaded,
warn the user that the session cwd will not follow the worktree and that subsequent
commands must use absolute paths / `git -C <path>` (do not sprinkle `cd`).

### Phase 2.5 — Persist the session title to `NAME`

Give the session a findable, durable title — the same effect as the user typing
`/rename <NAME>`. There is no callable tool for it, so write the underlying record
directly. `/resume`'s picker builds its title list by scanning each session's own
transcript file for `{"type":"custom-title","customTitle":...}` lines (falling back
to `ai-title` if none exist) — it does **not** read `~/.claude/sessions/<pid>.json`.
That pid file only drives the live "concurrent sessions" indicator while this process
is running, and gets deleted the instant the process exits, so writing only there
renames nothing durable — the change vanishes the moment the session ends.

Run the bundled script — one plain command, no heredoc (Principle 6):

```bash
python3 <skill-dir>/scripts/rename-session.py "$CLAUDE_CODE_SESSION_ID" "<NAME>"
```

(Substitute the real absolute path to this skill's `scripts/rename-session.py`.) It
appends the title records to the transcript and mirrors the name into the live pid
file, reporting each on stdout.

Earlier versions inlined this as `python3 - … <<'PY'`. Don't go back to that: a
heredoc is exactly the shape the worktree-isolation validator refuses, and improvising
around it means writing a scratch script to `/tmp` — two more round trips and a
`Write` that nothing grants.

Notes:
- The script appends rather than rewriting, because the transcript is being actively
  written by this very process for the rest of the session. Never read-modify-write it.
- If `CLAUDE_CODE_SESSION_ID` is unset or no transcript matches, the script prints a
  one-line skip and exits 0 — a missing name is not worth failing the session over.
- This renames the session for next time — it takes effect when the session is opened
  via `/resume` afterward. It does not repaint the *currently running* process's own
  terminal title or prompt-box name (only the interactive `/rename` command updates
  that in-memory state); the pid-file mirror is the closest live-visible approximation.

### Phase 2.6 — Report what the worktree inherited (read-only)

A fresh worktree is not empty of untracked state, and the state it gets can make it look
ready while pointing at another checkout's resources. Establish both, in the new cwd:

Issue these as **separate, parallel Bash calls in one message** (Principle 6) — joining
them with `;` is what gets the whole probe refused:

- **`.worktreeinclude`** at the *main checkout's* root: every non-comment line is a
  gitignored path Claude Code **copies** into the new worktree — usually `.env`. Read the
  file, then confirm what landed (`ls -la` each path in the worktree). Paths absent from
  the main checkout are skipped silently, so absence is not an error.
- **`worktree.symlinkDirectories`** in user settings: those directories (`node_modules`
  and friends) are **symlinked** back to the main checkout, not copied — so no install
  step is needed, and none should be run. Use the `Read` tool on
  `~/.claude/settings.json` rather than shelling out to `cat`/`grep`/`jq`.

Then answer the question that decides whether the workspace is usable: **does this
worktree have its own stack, or is it borrowing the main checkout's?** A copied `.env`
carries the source checkout's ports, `COMPOSE_PROJECT_NAME`, and `PGURL`/`DATABASE_URL`
verbatim. Until something reassigns them, `docker compose`, `just migrate`, `just test`,
and `just psql` run from this worktree reach the **main checkout's** containers and
database — silently, with no error to notice.

- **Repo allocates per-worktree ports** (look for it: `just --list | grep -i 'worktree.*port'`):
  say so and print the exact command, e.g. `just setup_worktree_ports 6320`. **Do not run
  it.** It claims a range of sequential ports, and only the user knows what their other
  worktrees already hold.
- **Repo has no such recipe:** say plainly that no per-worktree isolation exists — the
  stack has to be run from one checkout at a time, and starting it here will collide with
  or hijack whatever is already up.
- **No `.worktreeinclude` at the main root:** the worktree has no `.env`. Name the repo's
  bootstrap (`just setup`, `cp env.example .env`), or, when there is no `env.example`, say
  the file has to be reconstructed by hand — and note that a missing dotenv file is
  usually *silent*, leaving recipes with empty variables and hardcoded fallbacks rather
  than an error.

All read-only. Do not run `docker`, `just migrate`, or any stack command to determine this.

### Phase 3 — Load the JIRA story (only if `NAME` is a ticket)

1. Fetch the story with the Atlassian CLI, uppercased key, one call:

   ```bash
   acli jira workitem view <KEY> --json \
     --fields "summary,issuetype,status,assignee,priority,description,parent,issuelinks"
   ```

   Do **not** reach for the Atlassian MCP server — it is disabled, and
   `mcp__plugin_atlassian_atlassian__*` tools no longer exist.
2. If the command fails, note it in one line and go to Phase 4 — never block the
   worktree on it:
   - `command not found` → "acli not installed; skipping story load".
   - `unauthorized: use 'acli auth login'` → "acli not authenticated; skipping story
     load — run `! acli auth login`". Do not run `acli auth login` yourself; it is an
     interactive browser flow.
   - Unknown key or permissions → report the error verbatim in one line.
3. Read the issue and distill it — do not dump the raw payload. The `description` comes
   back as Atlassian Document Format (ADF) JSON, so read the text out of the node tree
   rather than pasting it. Summarize:
   - **Title / type / status** (one line).
   - **The implementation ask** — what the ticket wants built or changed, in your words.
   - **Acceptance criteria** if present, as a short checklist.
   - Notable links (design, parent epic, blocked-by) if any.

### Phase 4 — Report once, then stop

This is the *only* narration Phases 0-3 produce. Print a short summary, then wait:

- Worktree: `.claude/worktrees/<NAME>` · branch `worktree-<NAME>` · based on
  `origin/<default>`.
- Session renamed to `<NAME>` (or a one-line note if the rename was skipped).
- Inherited environment, from Phase 2.6: which `.worktreeinclude` paths were copied, which
  directories were symlinked, and — when the copied `.env` still points at the main
  checkout's stack — the exact port-allocation command to run before anything else. Put
  this above the handoff line. It is the one item that, if missed, sends `just migrate` or
  `just test` at the wrong database.
- If a ticket was loaded: the story summary and implementation ask from Phase 3.
- If not a ticket, or JIRA skipped: say so in one line.
- End with an explicit handoff, e.g. *"Workspace ready. What would you like to build?"*

**Then stop.** Do not begin implementation, exploration, or planning until the user
gives the next instruction.

## Reducing permission prompts

Claude Code plugins have no mechanism to self-grant permissions — every tool call
below is still gated by the *user's own* `settings.json` (project or
`~/.claude/settings.json`), never by anything this plugin ships. To run this skill
end-to-end without prompts, add to `permissions.allow`:

- `EnterWorktree`, `ExitWorktree` — the worktree lifecycle tools Phase 2 calls directly.
- `ToolSearch` — loads deferred tools (`EnterWorktree`); read-only.
- `Bash(acli jira workitem view *)` — Phase 3's story fetch; read-only.
- `Bash(git rev-parse *)`, `Bash(git worktree list)` — Phase 1's read-only preconditions
  (covered already if you blanket-allow `Bash(git *)`).
- `Bash(cat *)`, `Bash(ls *)`, `Bash(just *)` — Phase 2.6's probe of the inherited
  environment.
- Phase 2.5's rename runs under `python3`. There's no way to allowlist one script
  without allowlisting the interpreter broadly, so treat `Bash(python3 *)` as a
  deliberate, standalone trust decision, not something to add solely for this skill.

Note that Bash rules are wildcard-matched against the raw command string, where `*`
spans `/` and spaces — they are not gitignore-style path globs (that matcher is only
used for `Read`/`Edit` rules). And entering `auto` mode strips every `Bash(...)` allow
rule in favour of the classifier, so in that mode what matters is `autoMode.allow`,
not this list.

## Gotchas

- **EnterWorktree is deferred.** Calling it without a prior `ToolSearch
  select:EnterWorktree` fails with InputValidationError. Always load it first.
- **After EnterWorktree, compound Bash lines are refused.** The isolation validator
  rejects `;`, `&&`, `$(…)` and heredocs regardless of how harmless the components are
  — it is a static-analysis gate, not a permission check, so no allow rule and no
  permission mode gets past it. Split the call (Principle 6).
- **`acli` is a shell command, not a tool.** There is nothing to ToolSearch for; the
  Atlassian MCP server is disabled and its `mcp__plugin_atlassian_atlassian__*` tools do
  not exist.
- **Already in a worktree → EnterWorktree refuses** a new `name`. Don't nest; surface it.
- **Name rules are strict.** Spaces, `@`, `:` and other punctuation are rejected. Fix
  with the user rather than silently mangling the name.
- **`baseRef: fresh` needs the remote.** The base is a freshly-fetched origin default;
  if offline or the remote unreachable, EnterWorktree may fail — report it plainly.
- **Don't pre-create the branch.** EnterWorktree makes `worktree-<NAME>` itself; a prior
  `git checkout -b` of that name will collide with it.
- **`.worktreeinclude` is read from the main checkout's working tree**, not from the branch
  being checked out. One that exists only on a feature branch copies nothing, so a repo
  where it is still in review behaves as if the file were absent.
- **Copies, not symlinks.** Rotating `.env` in the main checkout does not reach worktrees
  that already exist, and each worktree is one more on-disk copy of real credentials.
- **Symlinked `node_modules` is shared, not private.** An install inside a worktree writes
  through to the main checkout's `node_modules`; a dependency bump here changes it there.
- **EnterWorktree locks the worktree**, and the lock can outlive the process that took it
  (`git worktree list --porcelain` shows `locked claude session <name> (pid …)`). Teardown
  needs `git worktree unlock <path>` first — plain `git worktree remove --force` fails with
  "cannot remove a locked working tree".
- **JIRA is optional.** A non-ticket name (`random-misc`) is a perfectly valid session;
  just skip Phase 3.
