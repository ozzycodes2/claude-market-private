---
name: fix
description: Apply and commit fixes for the findings a prior /review:review recorded — refactor code smells using the named Fowler/Kerievsky refactoring in the language's own idiom, rewrite flagged documentation and comments for clarity, regenerate stale generated artifacts, and defer anything needing a human design decision rather than guessing. Then answer the review comments that raised them: reply with the fix and resolve the thread once the commit is on the PR. Use after /review:review when you want the findings actually resolved in the working tree, one commit per finding. Edits files, commits, and replies on the PR; never pushes, never merges. Also the fix engine behind monitor-pr.
allowed-tools: Bash Read Write Edit Grep Glob Skill Task Agent
disable-model-invocation: false
---

# Fix Review Findings

`/review:review` names the refactoring that resolves each finding and then posts
it as a comment. This skill is the consumer that `required_actions` was written
for: it reads the durable findings ledger, applies each fix, commits one finding
at a time, and answers the comment that asked.

It **edits, commits, and replies on the PR. It never pushes.** Pushing belongs to
`monitor-pr`, which delegates its editing here. Because it does not push, it
resolves a thread only once that thread's commit is visible on the remote — see
Step 7.1.

## Inputs

```
/review:fix [<pr-number|pr-url>] [--repo owner/name]
            [--dry-run]            plan and partition only; write nothing
            [--max-concurrent N]   parallel agents, default 4
            [--force]              break a stale ledger lock
            [--ack-only]           skip Steps 1–6; only answer review comments
                                   for findings whose commits are already pushed
            [--no-ack]             fix and commit, write nothing to GitHub
            [--post-deferred]      post one PR comment for deferrals that have
                                   no thread to reply to (off by default)
            [--no-push]            no-op; documents the default so monitor-pr can be explicit
```

With no argument, infer the PR from the current branch (`gh pr view --json
number`). There is no `--only` or `--severity` flag: the scope is every open
finding. Selection is `status == "open"`, which also lets `monitor-pr` process
just the findings appended since its last tick.

## Step 0: Resolve the ledger

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ ! -f "$PLUGIN_ROOT/scripts/findings_ledger.py" ]; then
  PLUGIN_ROOT="$(cd "${CLAUDE_SKILL_DIR:-.}/../.." 2>/dev/null && pwd)"
fi
LEDGER_PY="$PLUGIN_ROOT/scripts/findings_ledger.py"

PR_NUMBER="${1:-$(gh pr view --json number -q .number)}"
LEDGER=$(python3 "$LEDGER_PY" path \
  --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner)" --pr "$PR_NUMBER")
RUN_ID="fix-$(date -u +%Y%m%dT%H%M%SZ)-$$"
```

`LEDGER_PY` is a path, and `python3` stays at the call site. Folding the
interpreter into the variable works in bash and silently breaks in zsh, which does
not word-split an unquoted expansion.

If the ledger is missing:

> No findings ledger for PR #\<N>. Run `/review:review <url>` first.

**Do not reconstruct one by scraping the posted review.** The inline-comment
round-trip loses `remedy`, `refactoring`, `drift_class`, and `code_says` — which
are exactly the fields that select a strategy.

## Step 1: Lock, reconcile, and establish green

### 1.1 Take the lock

```bash
python3 "$LEDGER_PY" lock --ledger "$LEDGER" --run "$RUN_ID"   # add --force to break a stale lock
```

One `fix` run per ledger, for the same reason `monitor-pr` allows one monitor per
PR: two runs on one branch means double commits and interleaved edits. A lock
older than two hours is stale — report it and offer `--force`.

### 1.2 Reconcile against git, not against the ledger

The ledger records what a previous run *believed*. Verify it:

- For each `committed` finding, `git cat-file -e <sha>^{commit}`. A sha that no
  longer exists (branch reset, worktree swap) demotes the finding to `open`.
- For each `claimed` or `applied` finding, check `git status --porcelain` for its
  recorded files — a previous run died mid-flight.
- **Hard stop if the tree is dirty with edits `fix` cannot attribute** to a
  finding in the ledger. Report the paths and ask. Never `git stash`, never
  `git restore` a path you did not write.
  - One exemption: `.claude/pr-monitor/pr-*.md`. That is `monitor-pr`'s tracker,
    written by the caller that just invoked this skill, so it is dirty on every
    delegated run. Leave it alone and never stage it — a monitor's scratch file
    has no business in a fix commit.
- For attributable in-flight edits, show the diff and ask: commit as-is, or
  discard and redo that finding.

### 1.3 Check the ledger is not stale

Compare `pr.head_sha` against current `HEAD`. If the branch has moved since the
review, **every `line` in the ledger is suspect.** Warn, and treat agent rule 5
(locate by content, not by line) as mandatory rather than advisory.

### 1.4 Establish a green baseline

```bash
# only when context.test_setup.can_run_safely is true
<context.test_setup.test_command>
```

**You cannot refactor on red.** If the baseline fails, nothing afterwards can
distinguish breakage this run caused from breakage it inherited. On a red
baseline, stop and report — unless the user asks to fix the baseline first, which
is its own finding.

Where `can_run_safely` is false there is no baseline and no iteration loop; see
`shared/fix-contract.md`.

## Step 2: Route every open finding

```bash
python3 "$LEDGER_PY" show --ledger "$LEDGER" --status open --json
```

Read `references/strategy-routing.md` and assign each finding exactly one
strategy: **S0** formatter, **S1** refactor, **S2** repair, **S3** prose, **S4**
comment, **S5** regenerate, **S6** defer. First match wins.

Every finding gets a strategy. Nothing is dropped. S6 is the honest-deferral
path, not a filter — if most findings land there, the routing is too lax and the
report must make that visible.

### Findings with no `path`

Common and deliberate: architectural findings and CI-ingested findings carry no
location. Do not guess a file and do not drop the finding.

1. If the `body` or `remedy` names a symbol, `rg` for it and derive the file set.
2. Confirm the symptom at the candidate before editing.
3. Zero candidates, or more than three → **S6** `ambiguous-remedy`.

**Never dispatch an agent with neither a file anchor nor a symbol.** That is how
this skill would rewrite half the repository.

## Step 3: Order the work

Per `references/strategy-routing.md`:

1. **S5 first** for any path S1/S3/S4 also touch — regeneration overwrites hand
   edits.
2. **S2** — correctness and security.
3. **S3, S4, S0.**
4. **S1 last** — where the suite could not run these are unverified, and at the
   tip of the branch an unwind is one `git revert`.
5. Within a sequential group, **descending line number.**

## Step 4: Dispatch

Partition open findings by **file set**. Disjoint sets get one agent each, all
dispatched in a single message. Findings sharing any file collapse into one
agent that handles them sequentially, re-reading the file between findings. Cap
concurrency at `--max-concurrent` (default 4).

**Agents edit; this skill commits and verifies.** There is one `.git/index` per
worktree, so concurrent commits from several agents interleave and a commit ends
up carrying another agent's half-finished work; and a test suite with shared
fixtures — a database it resets, a port it binds — corrupts the run when four
agents start it at once. The agent prompts forbid every `.git`-writing command
and every suite invocation; the orchestrator stages the reported paths and runs
the suite itself.

The partition is therefore both the concurrency unit and the verification unit.

Pin **both** `subagent_type` and `model` on every dispatch — an omitted `model`
inherits the session model and collapses the intended split:

| Strategy | `subagent_type` | `model` |
|---|---|---|
| S1 design-level | `general-purpose` | `opus` |
| S1 mechanical | `general-purpose` | `sonnet` |
| S2 | `general-purpose` | `opus` |
| S3, S4 | `general-purpose` | `sonnet` |

Use the verbatim prompts in `references/subagent-prompts.md`, with the catalog
row, the idiom rows, and the rules **inlined** — a subagent runs in the reviewed
repo and cannot resolve a path inside this skill.

S0, S5, and S6 need no agent: run the formatter, run the regeneration recipe, or
record the deferral.

### S5 — resolve the regeneration command

In order: a command named literally in `remedy`; an entry in
`context.build_system.commands`; a task-runner recipe whose name matches the
artifact. None resolves → **S6** `no-regen-command`. Commit only the generator's
output, and prove idempotence by running it twice (`git diff --exit-code` clean).

### S0 — run the repo's formatter, not a reported diff

A formatting finding may arrive with a diff attached — from a linter the security
scan ran, or from a CI job `monitor-pr` ingested. Treat it as evidence that drift
exists, discard the diff, and run `context.build_system.commands.lint` autofix:
the tool is authoritative and a review-time diff is stale by now. One batch
commit. No lint command → **S6** `no-lint-command`.

## Step 5: Commit per finding, verify per partition

Agents never run the suite. As each agent reports `applied`, commit its finding
as reported. After a partition's last commit, run
`context.test_setup.test_command` once.

Verifying per finding costs one suite run per finding; verifying per partition
costs one per partition. On a suite that takes minutes — which is most of them —
that difference is the dominant term in how long a fix round takes, and the
information it buys is recoverable: a red partition is a handful of commits, and
`git bisect` finds the guilty one in a couple of runs.

**When the partition goes red:**

1. `git bisect` across the partition's commits, using the suite as the test.
2. Re-dispatch that finding with the failure output attached. Adjust the change,
   never the test's expectations unless the finding is about the test.
   **Do not revert. Do not commit a WIP. Do not defer.**
3. Re-run the suite. Repeat until green.

**Never leave the branch red.** The claim each commit makes — that the branch is
green at that commit — is written at commit time and made true at partition
time. A fix round that ends red has not ended.

**When the loop stalls**, escalate rather than abandon: if the failure output
stops changing, re-dispatch on a stronger model with the full failure history. If
that also stalls, **surface the finding to the user as a live question and pause
on it.** Never silently defer it and never move on as though it were handled.

No runnable suite (`context.test_setup.can_run_safely` is false) → commit as
reported and say so in the Step 8 report; CI is the verification.

Commit per `shared/fix-contract.md` — headline, body, preservation line, trailer
— then record it:

```bash
python3 "$LEDGER_PY" resolve --ledger "$LEDGER" --id <ID> --sha "$(git rev-parse HEAD)" --strategy S1
```

## Step 6: Record deferrals

```bash
python3 "$LEDGER_PY" defer --ledger "$LEDGER" --id <ID> --reason <reason> \
  --decision "<the one-sentence question a human must answer>" --run "$RUN_ID"
```

A deferred finding gets **no edit and no commit**, keeps its original severity,
and never gets a bare `TODO` as a consolation prize. This skill does not file
tickets.

## Step 7: Answer the review comments

`/review:review` asked each of these questions as an inline comment. A finding
resolved in silence leaves the reviewer with an open thread and no idea it was
handled, so close the loop: reply to the comment that raised it, and resolve the
thread when the work is actually on the PR.

### 7.1 Only acknowledge what the PR can show

```bash
git fetch origin "$HEAD_BRANCH" --quiet
git merge-base --is-ancestor <sha> "origin/$HEAD_BRANCH"   # per committed finding
```

**A thread is resolved only when its commit is on the remote.** This skill does
not push, so on a normal run that check fails for everything it just committed —
and that is the correct outcome, not a bug. Resolving a thread for a commit that
exists only on this machine tells a reviewer to go look at something they cannot
see.

So the flow is: `fix` commits, you push, then acknowledgement happens:

```
/review:fix 123 --ack-only      # skip Steps 1–6; acknowledge pushed work only
```

Under `monitor-pr` this resolves itself — it calls `fix` before pushing, so
nothing is acknowledged here, and `monitor-pr` acknowledges in its Phase 3 after
its push. One acknowledgement per thread, from whoever can see the commit.

### 7.2 Map findings to threads

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        nodes{
          id isResolved isOutdated
          comments(first:1){ nodes{ databaseId author{login} path line originalLine body } }
        }
      }
    }
  }
}' -F owner="$OWNER" -F repo="$NAME" -F pr="$PR_NUMBER" \
  | python3 "$PLUGIN_ROOT/scripts/pr_threads.py" match --ledger "$LEDGER" --threads - --json
```

The script attributes a thread to `/review:review` by the Conventional Comments
marker its comments lead with (`**issue (blocking):** …`), so it works whichever
account posted the review. It pairs a thread with a finding on same-file plus
same-line or same-title, and returns `matched`, `ambiguous`,
`unmatched_findings`, `unmatched_threads`.

**Act only on `matched`.** An `ambiguous` entry means two findings fit one thread
equally well — report it and leave the thread alone. A wrong match answers a
reviewer's question with the resolution of a different question, which is worse
than leaving it open.

A `low` confidence match is still a match, but say so in the report so it can be
spot-checked. Findings with `reason: no-path` never had an inline comment — CI
failures and architectural findings — and are not a gap.

### 7.3 Reply, then resolve

Per `matched` entry, reply first. If the reply fails, do not resolve: a resolved
thread with no explanation is worse than an unresolved one.

```bash
gh api graphql -f query='mutation($t:ID!,$b:String!){
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t, body:$b}){
    comment{ url }
  }
}' -F t="<thread_id>" -F b="<body>"
```

**Committed** — one line of what changed, and the sha:

> Fixed in `<sha>` — extracted the retry loop into `Transport::send_with_retry`
> so the backoff lives with the transport. `<test_command>` passes.

**Deferred** — the question, not an apology. The thread stays open:

> Not fixed — this needs a decision first: outbox table, CDC, or accept the
> window? Each changes the failure mode, so picking one here would be a guess.

Then resolve, for `action: reply+resolve` only:

```bash
gh api graphql -f query='mutation($id:ID!){
  resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } }
}' -F id="<thread_id>"
```

Never resolve a `reply` action. A deferral is the one finding that most needs a
human to see it, and resolving it hides it.

Write the reply from the diff and the finding, not from this run's shape. No
strategy codes, no finding IDs, no "as requested" — the reviewer is reading a PR,
not this skill's output. `F012` means nothing to them.

### 7.4 Record it

```bash
python3 "$LEDGER_PY" ack --ledger "$LEDGER" --id <ID> --thread <thread_id> \
  --action reply+resolve --url "<reply url>" --run "$RUN_ID"
```

Idempotent per `(finding, thread)`, and the matcher skips anything already
recorded. That is what stops a re-run — or a `monitor-pr` tick after a manual
`fix` — from replying to the same reviewer twice.

`--no-ack` skips this whole step.

## Step 8: Report

```
Fix run complete — PR #<N>

Resolved (<n>):
  <sha>  refactor: move rate limiting into the transport   F003
  <sha>  docs: tighten the auth overview                   F007

Deferred (<n>):
  F012 · src/outbox.rs:88 · dual-write with no outbox —
         decision: outbox table, CDC, or accept the window?

Unverified (<n>):   # only when the suite could not run
  <sha>  F005 — suite not run (<safety_notes>); revert with `git revert <sha>`

Acknowledged (<n>):
  F003  replied + resolved   PRRT_x
  F012  replied, left open   PRRT_y   (deferred)

Not acknowledged (<n>):
  F007  commit not pushed — push, then `/review:fix <N> --ack-only`
  F009  ambiguous: PRRT_z fits F009 and F011 equally well
  F005  no inline comment to answer (CI finding)

Nothing was pushed. <n> commit(s) on <branch>, ahead of origin.
```

Then `python3 "$LEDGER_PY" unlock --ledger "$LEDGER"`.

Make the deferral count prominent. A run that defers most of its findings has
mis-routed them, and that has to be visible rather than buried.

Make **Not acknowledged** equally prominent. An unanswered thread is work the
reviewer cannot see, and the usual cause — nothing pushed — needs one command
from the user to fix.

`--post-deferred` posts one PR-level comment listing deferrals that had **no
thread to reply to**. Deferrals with a thread are answered in Step 7.3 instead,
where the reviewer who raised them is actually looking. Off by default.

## Deny-list

From `shared/fix-contract.md`, which is the single copy: never `git push`, never
`gh pr merge`, never force-push, never touch the default branch, never
`git reset --hard`, never `git rebase`, never `--amend` a pushed commit, never
`git stash`, never `--no-verify`. A pre-commit hook rejection is a finding to
report, not an obstacle to route around.

On GitHub, Step 7 is the whole permitted surface: reply in a review thread, and
resolve a thread whose commit is on the remote. Never resolve a thread this run
did not fix, never resolve a deferral, never dismiss a review, never edit or
delete someone else's comment, and never post a PR-level comment except the one
`--post-deferred` asks for.

One narrow exception, orchestrator-only: `git restore --source=HEAD -- <explicit
paths>` to discard a dead run's in-flight edits after the user confirms (Step
1.2), restricted to paths the ledger attributes to that finding.

## Notes

- Repo-agnostic by construction. Every command comes from the ledger's `context`
  block (`test_setup.test_command`, `build_system.commands.*`,
  `languages.primary`); nothing about a toolchain, a ticket format, or a
  directory layout is hardcoded.
- Resumable. State lives in the ledger, outside the repository, so it survives
  compaction, `git clean`, and worktree switches.
- Idempotent. A second run with no new findings makes no commits, replies to
  nobody twice, and says so.
- `monitor-pr` drives this skill for live CI failures and review threads; it
  keeps the polling and the push. Acknowledgement belongs to whichever of the two
  can see the commit on the remote — under `monitor-pr` that is always
  `monitor-pr`, because it calls this skill before pushing.
