---
name: monitor-pr
description: Continuously watch a GitHub PR (usually one Claude just opened) for CI failures and new review comments, and drive fixes as they arrive. Use when the user says "monitor this PR", "watch PR #45", "watch the PR for comments and check failures", "address review comments as they come along", "keep an eye on CI and fix failures", or after opening a PR and wanting it shepherded to green. Polls on an interval (drive with /loop), appends each finding to the durable findings ledger, delegates every edit and commit to /review:fix, pushes what it commits, resolves the bot review threads it addresses, and deletes the tracker once everything is handled. Gates suggestions and human comments for user confirmation instead of acting blindly.
allowed-tools: Bash Read Write Edit Skill ScheduleWakeup TaskCreate TaskUpdate
disable-model-invocation: true
---

# Monitor PR

Shepherd a Claude-authored PR to green without a human babysitting the tab. On a
repeating interval, poll the PR for **CI failures** and **new review comments**;
whatever is actionable becomes a ledger finding, is fixed and committed by
`/review:fix`, is pushed, and — for the bot's own review threads — gets resolved.
Suggestions and human comments are surfaced for a decision, never silently acted on.

**This skill edits no source file and commits nothing.** It polls, triages,
pushes, and talks to GitHub. Editing is `/review:fix`'s job.

## Core principles

1. **Baseline, then diff.** Snapshot the PR once at start. On every later tick,
   act only on what is *new or still-open* versus that baseline — never re-litigate a
   comment already handled or a check already green. (Learned the hard way:
   without a baseline the monitor churns on stale findings.)
2. **One monitor per PR.** Before starting, check for an existing tracker for this PR.
   If one is active, resume it — do **not** spin up a second loop. Two monitors on one
   PR means double subagents, double commits, confusion.
3. **The ledger is the source of truth; the tracker is a mirror.** Finding state
   lives in `~/.claude/review-findings/<owner>__<repo>/pr-<n>.json`, outside the
   repository and shared with `/review:fix`. The tracker is the human-readable view
   of it, carrying the same ledger IDs. When they disagree, the ledger is right.
4. **Fix what's yours; ask about the rest.** CI failures and the bot's own unresolved
   review threads are auto-fixed. Human review comments and nit/suggestion-level items
   are logged and reported for the user to decide — pause and ask before acting.
5. **Delegate the fixing.** Parallelism, partitioning, and the agent contract belong
   to `/review:fix`, which owns one lock per ledger and one commit per finding. This
   skill groups nothing, dispatches nothing, and edits nothing. Append the finding,
   call the skill, read the result back.
6. **Respect the permission deny-list** in `shared/fix-contract.md`, which is the
   single copy both skills work from. Never `gh pr merge`, never force-push, never
   `git reset --hard`, never touch the default branch. Fixes are pushed to the *PR
   branch*. Merging stays with the user; surface the command, don't run it.
   The one line that differs between the two callers: **`/review:fix` never pushes
   — the push is this skill's job**, and nothing it committed reaches GitHub until
   Phase 3 runs.

## Inputs

```
/monitor-pr <pr-number> [--repo owner/name] [--auto | --critical-only]
```

- `<pr-number>` — required. `--repo` defaults to current repo (`gh repo view`).
- Default mode: auto-fix **CI failures** + **unresolved bot review threads**; **gate**
  human comments and suggestions (log + report + ask).
- `--auto` — also act on human comments and suggestions without pausing.
- `--critical-only` — act only on CI failures and blocking bot threads; ignore nits.

Work happens in the PR's worktree/checkout. If the session isn't already there, check
out the PR branch first (`gh pr checkout <n>`); prefer running under a worktree from
`start-session`.

## The ledger and the tracker

### The ledger — where state lives

The same file `/review:review` writes and `/review:fix` consumes. Resolve its path
with the plugin script rather than composing it by hand:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ ! -f "$PLUGIN_ROOT/scripts/findings_ledger.py" ]; then
  PLUGIN_ROOT="$(cd "${CLAUDE_SKILL_DIR:-.}/../.." 2>/dev/null && pwd)"
fi
LEDGER_PY="$PLUGIN_ROOT/scripts/findings_ledger.py"
POLL="$PLUGIN_ROOT/skills/monitor-pr/scripts/poll-pr.sh"
LEDGER=$(python3 "$LEDGER_PY" path --repo "$REPO" --pr "$PR_NUMBER")
RUN_ID="monitor-$PR_NUMBER-$(date -u +%Y%m%dT%H%M%SZ)"
```

Both paths are absolute on purpose. The working directory is the **reviewed
repository**, not this plugin, so a bare `scripts/poll-pr.sh` finds nothing — or
worse, finds a same-named script in the repo under review.

`LEDGER_PY` holds the path only, and `python3` stays at the call site. Folding the
interpreter into the variable works in bash and silently breaks in zsh, which does
not word-split an unquoted expansion.

The ledger holds each finding's status, its `external_ref` (the check or thread it came
from), and its `resolved_by_sha` once fixed. It sits outside the repository, so it
survives compaction, `git clean`, and a worktree switch — and it is what lets the
monitor and the fixer agree on what is already done.

### The tracker — the human-readable mirror

Path: `.claude/pr-monitor/pr-<n>.md` (create the dir if needed). It exists so a
person can read the monitor's state at a glance. It is **not** the store: every row
carries the ledger ID it mirrors, and a disagreement is settled by re-reading the
ledger, never by editing the tracker to match a memory.

```markdown
# PR #<n> monitor — <owner/name>
branch: <head-branch> · mode: <default|auto|critical-only>
ledger: ~/.claude/review-findings/<owner>__<repo>/pr-<n>.json
baseline @ <first-poll>: checks=<pass/fail/pending> · threads bot=<n> human=<n> · reviewDecision=<...>
last poll: <ts> · last summary: <one line>

## Open
- [ ] F003 · ci · critical · check="build (rust)" · with review:fix
- [ ] F004 · review-bot · critical · thread=PRRT_x · src.rs:88 · with review:fix
- [ ] F005 · review-human · needs-decision · thread=PRRT_y · api.ts:12 · REPORTED, awaiting user
- [ ] F006 · review-bot · deferred by fix · decision: outbox table, CDC, or accept the window?

## Done
- [x] F001 · ci · check="lint" · <sha> · pushed @ <ts>
- [x] F002 · review-bot · thread=PRRT_z · <sha> · pushed, thread resolved @ <ts>
```

Rows carry no `owner=agent:…` — this skill owns no agents. A finding in flight is
"with review:fix", and its authoritative status is the ledger's.

Refresh it from `python3 "$LEDGER_PY" show` after each phase. **Delete it when Open is empty
and CI is green** — that is the signal the monitor's job is complete. The ledger
stays: it is the record of what was fixed, what was deferred, and why.

## Triage matrix

| Signal (from `poll-pr.sh`) | Default | `--auto` | `--critical-only` |
|---|---|---|---|
| CI check `failing` | fix | fix | fix |
| Bot thread, unresolved, blocking/critical | fix + resolve | fix + resolve | fix + resolve |
| Bot thread, nit/suggestion | report + ask | fix + resolve | ignore |
| Human review thread / requested change | report + ask | fix | report + ask |
| Human issue comment | report + ask | fix | report + ask |
| `pending` checks | wait (tighten interval) | wait | wait |
| all green, no open threads | converge → cleanup | converge | converge |

**fix** here means *append to the ledger and let `/review:fix` do it* — this skill
never edits. **report + ask** means the finding is not appended at all; it stays out
of the ledger until the user says otherwise. **ignore** appends nothing and asks
nothing.

"Blocking/critical" vs "nit": judge from the comment body and any `reviewDecision:
CHANGES_REQUESTED`. When unsure, treat a bot thread as fixable and a human thread as
needs-decision. Every **fix** in this table implies the Phase 3 acknowledgement — once
the fix is pushed, resolve the corresponding thread, or reply @author if it isn't
resolvable. This applies to human comments too, whenever their fix actually ships.

## Workflow

### Phase 0 — Start / resume (once)

1. If `.claude/pr-monitor/pr-<n>.md` exists → **resume**: read it, then reconcile
   against the ledger (`python3 "$LEDGER_PY" show --ledger "$LEDGER" --json`), which is
   authoritative. Skip re-baselining.
   Otherwise run `"$POLL" <n> [--repo …]`, write the baseline block, and
   append every currently-failing check and unresolved actionable thread to the
   ledger as in Phase 2.
2. **Check whether a ledger exists.** `/review:review` writes it; a PR that was
   never reviewed has none, and Phase 2 will create one with `--create`. A created
   ledger has an **empty `context` block** — no `test_setup.test_command`, so
   `/review:fix` has no local signal and commits unverified, leaning on CI. That is
   a real limitation, not a detail: say it in the announcement, and suggest
   `/review:review <pr-url>` first when the PR has not been reviewed.
3. Announce the monitor is live and the cadence, then begin the loop.

### Phase 1 — Poll (each tick)

Run the read-only snapshot:

```bash
"$POLL" <n> [--repo owner/name]     # JSON: checks, threads{bot,human}, reviewDecision, mergeStateStatus
```

Diff against the ledger. New failing checks and newly-unresolved threads become
findings to append in Phase 2; checks that went green and threads now
resolved/outdated move to `Done` in the tracker. Merged/closed PR → stop and clean up.

A finding already in the ledger as `deferred` is **not** new, however the poll looks
— `/review:fix` decided a human has to answer it. Leave it where it is.

### Phase 2 — Hand the findings to `/review:fix`

This skill writes no file in the repository and makes no commit. It converts what
the poll found into ledger entries and calls the fixer.

**1. Append each new actionable finding**, with the `external_ref` that is its
return path to GitHub. Dedupe is the ledger's job — an unresolved thread re-polled
every tick appends once.

A failing CI check, piped from the classifier
(`scripts/review_formatter.py`'s `classify_ci_failure`):

```bash
printf '%s' "$CI_JSON" | python3 "$LEDGER_PY" append --ledger "$LEDGER" --source ci \
  --create --pr-url "$PR_URL"
```

An unresolved review thread, from the `threads` array `poll-pr.sh` already returns:

```bash
printf '%s' "$THREADS_JSON" | python3 "$LEDGER_PY" append --ledger "$LEDGER" \
  --source review-thread --create --pr-url "$PR_URL"
```

`--create` is a no-op once the ledger exists, so both commands are safe every tick.

**Gated findings are never appended.** A human comment or a nit in default mode
stays out of the ledger entirely — appending it would hand `/review:fix` work the
user has not approved. Mark it `needs-decision` in the tracker, report it, and ask.
Only after the user agrees does it get appended.

Transient CI failures — a timeout, a network blip — classify as `info` and the
normalizer drops them. Nothing to fix; the next poll re-runs them.

**2. Call the fixer.**

```
Skill review:fix <n> --no-push
```

It takes the ledger lock, routes every `open` finding to a strategy, applies it,
makes one commit per finding, and runs the suite once per partition — iterating
until the branch is green before it returns. `--no-push` is its default —
pass it anyway, so the division of labour is visible at the call site.

Do not pass a finding list. Selection is `status == "open"`, which is exactly the
set just appended plus anything an earlier tick could not finish.

**3. Read the result back.**

```bash
python3 "$LEDGER_PY" show --ledger "$LEDGER" --status committed,deferred --json
```

Each `committed` finding carries `resolved_by_sha`; each `deferred` one carries
`deferral.decision_needed`. Mirror both into the tracker. A deferred finding is a
question for the user, not a retry — re-appending it next tick would loop forever.

If `/review:fix` pauses on a finding it could not get to green, it surfaces that
as a question. Pass it through to the user unchanged; do not re-run the fixer over
it and do not push a partial result past it.

### Phase 3 — Push, then close the loop

`/review:fix` left its commits on the local head branch. Nothing has reached GitHub
yet, so CI has not re-run and no thread can honestly be resolved.

0. **Push the head branch.**

   ```bash
   git -C "$WORKTREE" push origin HEAD
   ```

   Never `--force`, never `--force-with-lease`, never a refspec naming the default
   branch. A rejected push means the remote moved: pull with rebase off, inspect,
   and report — do not resolve any thread, because the fix is not on the PR.

   Push once per tick, after the fixer returns, not once per commit. Each push
   triggers CI.

1. Mark every finding the push carried `pushed` in the tracker, against its sha.
2. **Always acknowledge the comment that prompted the work** — non-negotiable once the
   fix is on the PR branch, for **bot and human** comments alike. The handle is in
   the finding's `external_ref` (`thread_id`, `comment_id`, `author`), which is why
   it is recorded at append time and survives the round trip through the fixer.

   **Skip any finding that already carries an `acknowledged` entry for that
   thread.** `/review:fix` can also reply and resolve — for work that was already
   pushed when it ran, or when a user invoked it directly with `--ack-only` — and
   the ledger is what keeps one reviewer from being answered twice. Record each
   acknowledgement the same way:

   ```bash
   python3 "$LEDGER_PY" ack --ledger "$LEDGER" --id <ID> --thread <thread_id> \
     --action reply+resolve --run "$RUN_ID"
   ```

   A **deferred** finding gets a reply stating the decision it needs, and the
   thread stays **open**. Resolving it would hide the one finding that most needs
   a human.
   - **Inline / resolvable review thread** → resolve it:
     ```bash
     gh api graphql -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } } }' -F id="<threadId>"
     ```
   - **Not inline / not resolvable** (a PR-level issue comment, or any comment with no
     resolve handle) → reply with a **new comment that @-mentions the original author**
     and points at the fix:
     ```bash
     gh pr comment <n> --body "@<author> addressed in <sha> — <one-line of what changed>."
     ```
     To reply *inside* an existing review thread instead of at PR level:
     ```bash
     gh api repos/<owner>/<repo>/pulls/<n>/comments/<comment-id>/replies -f body="@<author> addressed in <sha> — …"
     ```
3. Let CI re-run; the next poll confirms green or surfaces a follow-up failure.

### Phase 4 — Converge and clean up

When `Open` is empty **and** CI is green **and** no unresolved actionable threads
remain:

- Post/keep a short summary: what was fixed, what was pushed, what still needs the user
  (gated items, deferrals from `/review:fix`, merge).
- **Delete the tracker** `.claude/pr-monitor/pr-<n>.md`. **Keep the ledger** — it
  records what was fixed and what was deferred, and a reopened PR resumes from it.
- Release the fixer's lock if a killed run left one:

  ```bash
  python3 "$LEDGER_PY" unlock --ledger "$LEDGER"
  ```
- Stop scheduling further ticks. If `mergeStateStatus` is `BLOCKED` only on approval,
  say so — do not attempt the merge.

## Cadence — drive with `/loop`

Built to run as a loop. Drive it with the **`/loop`** skill: each firing
re-enters and runs one Phase 1→3 tick. Under the hood that uses `ScheduleWakeup` for
dynamic pacing — if you aren't launched via `/loop`, self-schedule the next tick with
`ScheduleWakeup`.

Pick the interval by what you're waiting on (align to the prompt-cache window):

- **CI running / fixes in flight** → ~**240s** (checks resolve in minutes; stays cache-warm).
- **Idle, awaiting human review** → ~**1200–1800s** (nothing changes minute-to-minute).
- Stop the loop entirely at Phase 4, or if the PR is merged/closed.

Always pass the same `/monitor-pr <n>` prompt back so the next firing repeats the tick.

## Gotchas

- **No `Agent` in `allowed-tools`, deliberately.** Dispatch belongs to `/review:fix`,
  which pins `subagent_type` *and* `model` per strategy. An agent launched from here
  would inherit the session model and commit from a second `.git/index`.
- **Deferred tools.** `ScheduleWakeup` is native. If you track in-flight work with
  `TaskCreate`/`TaskUpdate`, the **ledger** stays the source of truth (it survives
  compaction; task state may not).
- **`poll-pr.sh` mutates nothing.** It only reads. Appending, pushing, and thread
  resolution are your job, per the matrix; editing and committing are not.
- **Bot detection.** The script flags authors containing `claude-code-action` or ending
  `[bot]` as bots. If this repo's Claude reviewer uses a different login, pass it via
  `CLAUDE_BOT=<substring>`.
- **Don't append outdated threads.** `isOutdated: true` usually means the code moved
  on; verify before spending a fix run on it.
- **The fixer needs a clean tree**, and hard-stops on edits it cannot attribute to
  a ledger finding. It exempts `.claude/pr-monitor/pr-*.md` for exactly this
  reason — the tracker is dirty on every delegated run. Anything *else* left
  uncommitted will stop the fixer and surface as a question.
- **Suggestion rounds.** A poll surfacing only nits/human comments in default mode is
  a *report*, not a work order — summarize and wait for the user.
- **One PR, one tracker, one loop.** Re-invoking on a PR that already has a tracker
  resumes it; it never starts a parallel monitor.
