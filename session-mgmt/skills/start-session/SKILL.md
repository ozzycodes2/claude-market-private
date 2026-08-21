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
  available and summarizes the implementation ask. Also renames the session to the
  argument (the same effect as `/rename <NAME>`) so it's easy to find in `/resume`.
  Then stops and waits for the user's instructions — it sets up the workspace and
  context, it does not start implementing.
license: MIT
compatibility: >-
  Requires a git repo (EnterWorktree branches off a fresh origin default; honors
  worktree.baseRef: fresh). JIRA loading is optional and needs the Atlassian plugin
  (atlassian@machinify-plugins) enabled. EnterWorktree and the Atlassian MCP tools
  are deferred — load them via ToolSearch before calling.
argument-hint: "<worktree/branch name — a JIRA key like COB-103, or any slug like random-misc>"
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
2. **The argument is the name — verbatim.** Whatever the user passes (`COB-103`,
   `random-misc`) is the worktree directory name *and* the local branch name. Do not
   rename, slugify, or prefix it. EnterWorktree names the branch after the worktree.
3. **Load context, don't act.** Create the worktree, load the story if there is one,
   report, then **stop and wait**. Do not read the codebase for an implementation plan,
   do not write code, do not enter plan mode — unless the user asks next.
4. **Degrade gracefully.** JIRA loading is a bonus, not a gate. If the argument isn't a
   ticket, or the Atlassian plugin isn't available, skip that step with a one-line note
   and still deliver the worktree.
5. **Rename the session to `NAME`.** `/rename` is a user-typed command with no callable
   tool. What actually makes a name show up in `/resume` is a `custom-title` record
   appended to the session's own transcript JSONL file — not the `name` field of
   `~/.claude/sessions/<pid>.json`. That pid file only drives the live "concurrent
   sessions" indicator while the process runs, and is deleted the instant the process
   exits, so writing it alone renames nothing durable. Write the transcript record
   directly (see Phase 2.5); mirror into the pid file too, best-effort, for the live
   indicator.
6. **Execute silently; report once.** Don't narrate phase transitions, tool calls, or
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
  (e.g. `COB-103`, `SUBRO-1505`). Uppercase it for the JIRA lookup only — the worktree
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
   a new branch `<NAME>`, based on a freshly-fetched origin default branch
   (`worktree.baseRef: fresh`), and switches the session cwd into it.
3. Do **not** run `git worktree add`, `git checkout -b`, or any `cd`. The tool does all
   of it; the branch is created for you.

**Fallback (only if EnterWorktree unavailable):** create the worktree at the
conventional path — `git worktree add .claude/worktrees/<NAME> -b <NAME> origin/<default>`
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

Find *this* session's transcript by matching the filename to the session id (never
guess the project-dir slug — its encoding isn't a stable contract):

```bash
python3 - "$CLAUDE_CODE_SESSION_ID" "<NAME>" <<'PY'
import json, sys, os, glob
sid, name = sys.argv[1], sys.argv[2]
matches = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
if not matches:
    print("no transcript file matched; skipping rename")
else:
    with open(matches[0], "a") as f:
        f.write(json.dumps({"type": "custom-title", "customTitle": name, "sessionId": sid}) + "\n")
        f.write(json.dumps({"type": "agent-name", "agentName": name, "sessionId": sid}) + "\n")
    print("renamed session ->", name)
PY
```

Then, best-effort, mirror the name into the live pid file too, so any concurrent
sessions view reflects it immediately while this process keeps running (purely
cosmetic — safe to skip on failure):

```bash
python3 - "$CLAUDE_CODE_SESSION_ID" "<NAME>" <<'PY'
import json, sys, os, glob, tempfile
sid, name = sys.argv[1], sys.argv[2]
d = os.path.expanduser("~/.claude/sessions")
for p in glob.glob(os.path.join(d, "*.json")):
    try:
        j = json.load(open(p))
    except Exception:
        continue
    if j.get("sessionId") == sid:
        j["name"] = name
        fd, tmp = tempfile.mkstemp(dir=d)
        with os.fdopen(fd, "w") as f:
            json.dump(j, f)
        os.replace(tmp, p)
        break
PY
```

Notes:
- Append, don't rewrite. The transcript file is being actively written by this very
  process for the rest of the session; a single `open(..., "a")` write is one
  `write(2)` call under `O_APPEND`, which can't corrupt or race with the process's
  own appends. Never read-modify-write this file the way the pid file is handled.
- Match the transcript by filename (`<sessionId>.jsonl`) under `~/.claude/projects/*/`
  — never by reconstructing the project-dir slug.
- If `CLAUDE_CODE_SESSION_ID` is unset or no transcript file matches, print the
  one-line skip and continue — a missing name is not worth failing the session over.
- This renames the session for next time — it takes effect when the session is opened
  via `/resume` afterward. It does not repaint the *currently running* process's own
  terminal title or prompt-box name (only the interactive `/rename` command updates
  that in-memory state); the pid-file mirror above is the closest live-visible
  approximation.

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

### Phase 4 — Report once, then stop

This is the *only* narration Phases 0-3 produce. Print a short summary, then wait:

- Worktree: `.claude/worktrees/<NAME>` · branch `<NAME>` · based on `origin/<default>`.
- Session renamed to `<NAME>` (or a one-line note if the rename was skipped).
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
- `ToolSearch` — loads deferred tools (`EnterWorktree`, the Atlassian tools); read-only.
- `Bash(git rev-parse *)`, `Bash(git worktree list)` — Phase 1's read-only preconditions
  (covered already if you blanket-allow `Bash(git *)`).
- Phase 2.5's rename scripts run under `python3`. There's no way to allowlist just
  those two scripts without allowlisting `python3` broadly — it's a general-purpose
  interpreter, so treat `Bash(python3 *)` as a deliberate, standalone trust decision,
  not something to add solely for this skill.

## Gotchas

- **EnterWorktree and the Atlassian tools are deferred.** Calling them without a prior
  `ToolSearch select:<name>` fails with InputValidationError. Always load first.
- **Already in a worktree → EnterWorktree refuses** a new `name`. Don't nest; surface it.
- **Name rules are strict.** Spaces, `@`, `:` and other punctuation are rejected. Fix
  with the user rather than silently mangling the name.
- **`baseRef: fresh` needs the remote.** The base is a freshly-fetched origin default;
  if offline or the remote unreachable, EnterWorktree may fail — report it plainly.
- **Don't pre-create the branch.** EnterWorktree makes the branch; a prior
  `git checkout -b <NAME>` will collide with it.
- **JIRA is optional.** A non-ticket name (`random-misc`) is a perfectly valid session;
  just skip Phase 3.
