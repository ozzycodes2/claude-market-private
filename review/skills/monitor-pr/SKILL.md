---
name: monitor-pr
description: Continuously watch a GitHub PR (usually one Claude just opened) for CI failures and new review comments, and drive fixes as they arrive. Use when the user says "monitor this PR", "watch PR #45", "watch the PR for comments and check failures", "address review comments as they come along", "keep an eye on CI and fix failures", or after opening a PR and wanting it shepherded to green. Polls on an interval (drive with /loop), records every finding in a scratch-file issue tracker, dispatches subagents to fix — in parallel when the work is independent — resolves bot review threads it addresses, and deletes the tracker once everything is handled. Gates suggestions and human comments for user confirmation instead of acting blindly.
allowed-tools: Bash Read Write Edit Skill Agent ScheduleWakeup TaskCreate TaskUpdate
---

# Monitor PR

Shepherd a Claude-authored PR to green without a human babysitting the tab. On a
repeating interval, poll the PR for **CI failures** and **new review comments**;
whatever is actionable becomes a tracked finding, gets fixed by a subagent (in
parallel when independent), and — for the bot's own review threads — gets resolved.
Suggestions and human comments are surfaced for a decision, never silently acted on.

## Core principles

1. **Baseline, then diff.** Snapshot the PR once at the start. On every later tick,
   act only on what is *new or still-open* versus that baseline — never re-litigate a
   comment already handled or a check that was already green. (Learned the hard way:
   without a baseline the monitor churns on stale findings.)
2. **One monitor per PR.** Before starting, check for an existing tracker for this PR.
   If one is active, resume it — do **not** spin up a second loop. Two monitors on one
   PR means double subagents, double commits, and confusion.
3. **The scratch file is the source of truth.** Every finding, its severity, owner
   subagent, and status live in the tracker. It survives compaction and lets a resumed
   monitor know exactly what is in flight.
4. **Fix what's yours; ask about the rest.** CI failures and the bot's own unresolved
   review threads are auto-fixed. Human review comments and nit/suggestion-level items
   are logged and reported for the user to decide — pause and ask before acting.
5. **Parallelize independent work.** Findings that touch disjoint files/areas get one
   subagent each, launched together. Findings that overlap are serialized to avoid
   clobbering each other's commits.
6. **Respect the permission deny-list.** Never `gh pr merge`, never force-push `main`,
   never `git reset --hard`. Fixes are pushed to the *PR branch*. Merging stays with the
   user; surface the command, don't run it.

## Inputs

```
/monitor-pr <pr-number> [--repo owner/name] [--auto | --critical-only]
```

- `<pr-number>` — required. `--repo` defaults to the current repo (`gh repo view`).
- Default mode: auto-fix **CI failures** + **unresolved bot review threads**; **gate**
  human comments and suggestions (log + report + ask).
- `--auto` — also act on human comments and suggestions without pausing.
- `--critical-only` — act only on CI failures and blocking bot threads; ignore nits.

Work happens in the PR's worktree/checkout. If the session isn't already there, check
out the PR branch first (`gh pr checkout <n>`); prefer running under a worktree from
`start-session`.

## The tracker (scratch file)

Path: `.claude/pr-monitor/pr-<n>.md` (create the dir if needed). Format:

```markdown
# PR #<n> monitor — <owner/name>
branch: <head-branch> · mode: <default|auto|critical-only>
baseline @ <first-poll>: checks=<pass/fail/pending> · threads bot=<n> human=<n> · reviewDecision=<...>
last poll: <ts> · last summary: <one line>

## Open
- [ ] F3 · ci · critical · check="build (rust)" · owner=agent:ab12 · in-progress
- [ ] F4 · review-bot · critical · thread=PRRT_x · src.rs:88 · owner=agent:cd34 · in-progress
- [ ] F5 · review-human · needs-decision · thread=PRRT_y · api.ts:12 · REPORTED, awaiting user

## Done
- [x] F1 · ci · check="lint" · fixed+pushed @ <ts>
- [x] F2 · review-bot · thread=PRRT_z · fixed+pushed, thread resolved @ <ts>
```

Update it on every state change. **Delete it when Open is empty and CI is green** — that
is the signal the monitor's job is complete.

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

"Blocking/critical" vs "nit": judge from the comment body and any `reviewDecision:
CHANGES_REQUESTED`. When unsure, treat a bot thread as fixable and a human thread as
needs-decision. Every **fix** in this table implies the Phase 3 acknowledgement — once
the fix is pushed, resolve the corresponding thread, or reply @author if it isn't
resolvable. This applies to human comments too, whenever their fix actually ships.

## Workflow

### Phase 0 — Start / resume (once)

1. If `.claude/pr-monitor/pr-<n>.md` exists → **resume** (read it; skip re-baselining).
   Otherwise run `scripts/poll-pr.sh <n> [--repo …]`, write the baseline block, and
   record every currently-failing check / unresolved thread as an initial finding.
2. Announce the monitor is live and the cadence, then begin the loop.

### Phase 1 — Poll (each tick)

Run the read-only snapshot:

```bash
scripts/poll-pr.sh <n> [--repo owner/name]     # JSON: checks, threads{bot,human}, reviewDecision, mergeStateStatus
```

Diff against the tracker. New failing checks and newly-unresolved threads become new
`Open` findings; checks that went green and threads that are now resolved/outdated move
to `Done`. Merged/closed PR → stop and clean up.

### Phase 2 — Dispatch fixes

For each actionable `Open` finding with no owner:

- Group by area. Independent findings → launch one `Agent` **each, in a single message**
  so they run concurrently. Overlapping findings → one agent, handled in sequence.
- Record the agent id as the finding's `owner` and mark it `in-progress`.

Subagent contract (put this in the Agent prompt):

> You are fixing one finding on PR #`<n>` in `<worktree path>`. Finding: `<check name
> or thread body + file:line>`. Reproduce it, make the **minimal** correct fix, add/adjust
> tests to keep coverage, run the relevant checks locally, then commit (ticket-prefixed
> conventional message, `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`) and
> push to the PR branch — do **not** merge, do **not** touch `main`, do **not**
> force-push. Report the commit sha and what you changed.

Gated findings (human / suggestion in default mode): do **not** dispatch. Mark
`needs-decision`, add to the report, and ask the user.

### Phase 3 — Close the loop on a fix

When a subagent reports the fix is committed **and pushed**:

1. Mark the finding `fixed+pushed` in the tracker.
2. **Always acknowledge the comment that prompted the work** — non-negotiable once the
   fix is on the PR branch, for **bot and human** comments alike:
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
  (gated items, merge).
- **Delete the tracker** `.claude/pr-monitor/pr-<n>.md`.
- Stop scheduling further ticks. If `mergeStateStatus` is `BLOCKED` only on approval,
  say so — do not attempt the merge.

## Cadence — drive with `/loop`

This skill is built to run as a loop. Drive it with the **`/loop`** skill: each firing
re-enters and runs one Phase 1→3 tick. Under the hood that uses `ScheduleWakeup` for
dynamic pacing — if you aren't launched via `/loop`, self-schedule the next tick with
`ScheduleWakeup`.

Pick the interval by what you're waiting on (align to the prompt-cache window):

- **CI running / fixes in flight** → ~**240s** (checks resolve in minutes; stays cache-warm).
- **Idle, awaiting human review** → ~**1200–1800s** (nothing changes minute-to-minute).
- Stop the loop entirely at Phase 4, or if the PR is merged/closed.

Always pass the same `/monitor-pr <n>` prompt back so the next firing repeats the tick.

## Gotchas

- **Deferred tools.** `ScheduleWakeup` is native; subagents use `Agent`. If you track
  in-flight fixes with `TaskCreate`/`TaskUpdate`, the tracker file still stays the source
  of truth (it survives compaction; task state may not).
- **`poll-pr.sh` mutates nothing.** It only reads. Fixes, pushes, and thread resolution
  are your job, per the matrix.
- **Bot detection.** The script flags authors containing `claude-code-action` or ending
  `[bot]` as bots. If this repo's Claude reviewer uses a different login, pass it via
  `CLAUDE_BOT=<substring>`.
- **Don't act on outdated threads.** `isOutdated: true` usually means the code moved on;
  verify before spending a subagent.
- **Suggestion rounds.** A poll that surfaces only nits/human comments in default mode is
  a *report*, not a work order — summarize and wait for the user.
- **One PR, one tracker, one loop.** Re-invoking on a PR that already has a tracker
  resumes it; it never starts a parallel monitor.
