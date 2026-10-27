# Fix contract — rules for agents that edit, and for the commits they produce

The single copy of these rules. `review:fix` owns the fix loop; `monitor-pr`
delegates to it. Both read this file, so the two cannot drift apart — an earlier
version of `monitor-pr` dispatched fix agents without pinning `model`, directly
against the warning in `skills/review/SKILL.md`, precisely because it carried its
own copy of the contract.

## Who may write what

| | Fixing agent | Orchestrator (`review:fix`) | `monitor-pr` |
|---|---|---|---|
| Edit working-tree files | **yes** | yes (mechanical strategies) | no |
| Write to `.git` | **never** | yes | no |
| Commit | **never** | yes, one per finding | no |
| Run the test suite | **never** | yes, once per partition | no |
| Push | never | yes — PR head branch, green tree, unless `--no-push` | yes |
| Reply in a review thread | never | yes, for pushed work | yes |
| Resolve a review thread | never | yes, for pushed work | yes |
| Any other GitHub state | never | never | yes |

**Agents edit; the orchestrator commits.** There is one `.git/index` per
worktree, so concurrent `git add` / `git commit` from several agents interleaves
and a commit ends up carrying another agent's half-finished edits. That breaks
one-commit-per-finding, which is the whole point of the design. The orchestrator
stages the paths an agent reports and commits them itself.

## Who answers the review comment

Both callers can reply and resolve, so they need a rule that cannot double-fire.

**Acknowledge only what the remote can show.** A thread is resolved only once its
commit is an ancestor of `origin/<head-branch>`. Resolving a thread for a commit
that exists on one machine tells a reviewer to look at something they cannot see.

That single rule partitions the work, and `--no-push` decides which side each
caller lands on:

- Invoked directly, `review:fix` pushes the green branch itself, so the check
  passes for its own commits and it acknowledges them in the same run. A run
  that could not push — red suite, diverged branch, `--no-push` — acknowledges
  nothing, and `--ack-only` completes it after the user pushes.
- Under `monitor-pr`, `fix` is called with `--no-push` and *before* the push, so
  it acknowledges nothing and `monitor-pr` acknowledges after its own push.

The ledger is the backstop. Every acknowledgement is recorded with
`findings_ledger.py ack`, which is idempotent per `(finding, thread)`, and the
matcher skips any finding already recorded. A reviewer is never replied to twice,
even if both callers try.

**Never resolve a deferral.** Reply with the decision it needs and leave the
thread open — it is the one finding that most needs a human to see it.

**Never resolve a thread this run did not fix.** An unresolved thread is a
question; a wrongly resolved one is a false answer, and the reviewer has no way
to tell.

## Agent rules

1. **Scope is this finding.** Touch no file the finding does not require. Fix no
   adjacent smell you notice — report it under `adjacent` and leave it. Someone
   reading `git log` must be able to map one commit to one finding.
2. **Behavior-preserving, for a refactoring.** Same inputs, same outputs, same
   side effects, same error values. If resolving the finding *requires* changing
   observable behavior, stop and report `needs-decision`. Do not change behavior
   and call it a refactoring. (Repair findings are the opposite: the behavior
   change is the point, and it needs a test.)
3. **Add no trait, interface, generic, type parameter, or layer of indirection
   that the smell does not demand.** The catalog's move is a starting point, not
   a quota. Where the language's idiom diverges from the catalog's
   object-oriented move, the idiom wins — and say which you applied, and why.
4. **Locate by content, not by line.** A finding's line number may predate
   commits made earlier in the same run. Confirm the symptom is really at that
   location before editing. If you cannot find it, report `not-reproducible` —
   never edit a plausible-looking substitute.
5. **Never write to `.git`.** No `add`, `commit`, `stash`, `checkout`,
   `restore`, `reset`, `rebase`, `push`. Leave your edits in the working tree
   and report the paths.
6. **Never run the test suite** (see below). Pure checks that write nothing and
   take no lock — a type check, a linter in check mode — are fine.
7. **Never narrate your change in a comment.** No `// fixed`, no `// now
   handles the edge case`, no address to a reviewer. That belongs in the commit
   message; git remembers. If your change makes an existing comment wrong,
   correct it from the code — or delete it.
8. **Apply the move with a tool when one covers it.** A refactoring engine or
   an analyzer autofix resolves every reference the same way each run; a hand
   edit is only as good as the agent's reading of each site. The tool rows are
   in `skills/fix/references/refactoring-tools.md`. Run a tool only on paths
   inside the finding's file set — a project-wide fixer is the orchestrator's,
   like the formatter.

### Report

The last thing an agent outputs, exactly these keys:

```
outcome:             applied | needs-decision | not-reproducible
files_changed:       repo-relative paths, newline-separated, or "none"
refactoring_applied: catalog name, or "none"
tool_applied:        the exact command run, or "none — <why>"
idiom_divergence:    one line, or "none"
behavior_preserved:  yes | no — and how you established it
verification:        the reason to believe the change is correct — the invariant
                     it preserves, the call sites you read, the pure check you
                     ran. Not a suite result; you did not run one.
decision_needed:     needs-decision only — the one-sentence question a human
                     must answer, each option, and its consequence
adjacent:            smells seen and not touched, or "none"
```

## Red, green, refactor

**You cannot refactor on red.** The orchestrator establishes a green baseline
before the first finding. If the suite is already failing, that is the first
thing to resolve — or stop and say so. Refactoring discipline against a red
suite is meaningless, because nothing distinguishes the breakage you caused from
the breakage you inherited.

**Only the orchestrator runs the suite, once per partition.** Agents run
concurrently and a suite with shared fixtures — a database it truncates, a port
it binds, a temp dir it clears — corrupts every other agent's run when a second
copy starts. Even where it is safe, verifying per finding costs one suite run
per finding instead of one per partition; on a suite that takes minutes that is
the dominant term in a fix round's wall clock.

The information is recoverable. A red partition is a handful of commits, and
`git bisect` across them finds the guilty one in a couple of runs — cheaper than
the runs that would have caught it eagerly.

### When the partition goes red

1. `git bisect` across the partition's commits, with the suite as the test.
2. Re-dispatch that finding with the failure output attached. Adjust *the
   change* — not the test's expectations, unless the finding is itself about the
   test. A failing test is not a reason to revert, not a reason to commit a WIP,
   and not a reason to defer the finding.
3. Re-run the suite. Repeat until green.

The only other exit is **the failure is not attributable to this run** — it was
already failing, it is a flake, it is an environment problem. That is a
different finding; say so and hand it back.

**Never leave the branch red.** Each commit claims the branch is green at that
commit; the claim is written at commit time and made true at partition time. A
fix round that ends red has not ended.

### When the loop stalls

Escalate rather than abandon. If the failure output stops changing across
iterations, the agent has run out of new information and is permuting. The
orchestrator re-dispatches the finding on a stronger model with the failure
history attached. If that also stalls, surface the finding to the user as a live
question and **pause on it** — do not silently defer it, and do not move on
pretending it was handled.

### When there is no local signal

If `context.test_setup.can_run_safely` is false, there is nothing to verify
against, so the partition run is skipped too. Apply each change once, carefully,
and commit it — CI is the backstop. The commit body must say the suite was not
run, and why. Run the lint command instead if it is a pure check that writes
nothing.

## Commit rules

One commit per resolved finding.

### Headline

```
[<TICKET>: ]<prefix>: <message>
```

**Ticket prefix**, resolved generically — never a hardcoded project key:

1. A branch-name segment matching `^[A-Z][A-Z0-9]+-[0-9]+` (e.g. `ABC-123` from
   `ABC-123-add-auth`).
2. Otherwise, infer from `git log -n 30 --pretty=%s`: if ≥60% of recent subjects
   share a leading-token pattern, follow it.
3. Otherwise omit. A session-level or repository-level convention outranks both.

**Prefix by strategy** — restricted to the conventional-commits set, or to the
narrower set the repository actually uses:

| Strategy | Prefix |
|---|---|
| Refactor | `refactor` |
| Repair (behavior change) | `fix` |
| Prose, comments | `docs` |
| Regenerate | `chore` |
| Formatter | `style`, or `chore` where the repo does not use `style` |

**Message** from the finding's title: ~50 characters, lowercase, imperative.
**Never the finding ID.** `F012` means nothing to someone hitting this line in
`git blame` in two years, and it is a leaked frame — it describes the review run,
not the code. The ID belongs in the ledger as `resolved_by_sha`.

### Body

Inverted pyramid, hard-wrapped at 80 characters.

- **Lede** — what changed and why, stated in the repository's own terms. Give the
  symptom as a fact about the code: *"The handler read three private fields of
  `Config` to compute a value `Config` could compute itself."* Never *"addresses
  review finding"*, never *"as flagged in review"*. The reader has the repo and
  nothing else.
- **Second paragraph** only when the design choice was non-obvious — the idiom
  you picked over the catalog's move, an alternative you rejected, or background
  the diff cannot show: *"Modeled the three states as an enum rather than a trait
  hierarchy; the arms are closed, so exhaustiveness is compiler-checked."*
- **Bullets** only for picky details, edge cases, or a deliberate non-change
  worth recording.

### The behavior-preservation line

A refactoring commit claims the behavior did not change. State how that was
established, because an unbacked claim is worse than no claim:

| Situation | Line |
|---|---|
| Refactor, green | `Behavior-preserving; <test command> passes unchanged.` |
| Refactor, tool-applied | Prefix either line above or below with `Applied by \`<tool_applied>\`.` |
| Refactor, green after a red partition | `Behavior-preserving; <test command> passes. Reached after N iterations; the first attempt <one clause on what was wrong>.` |
| Refactor, no local suite | `Behavior-preserving refactoring. Suite not run locally (<reason>); CI gates it.` |
| Repair | **No preservation claim.** State the before and after behavior, and name the test that now covers it. |
| Prose / comments | None. Add `No code change.` when only comments moved. |
| Regenerate | `Regenerated by \`<recipe>\`. Do not hand-edit.` |
| Formatter | `Formatter output only; \`<lint command>\`.` |

References such as `Fixes #12` go at the **end** of the body, never in the
headline — the headline's ~50 characters are for the change itself.

Trailer:

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Deny-list

Never, at any level:

- `git push`, except one case: a fast-forward push of the PR's own head branch
  to `origin`, from a verified-green tree, by `monitor-pr` or by `review:fix`
  without `--no-push`. A rejected push is reported, never forced or rebased
  around.
- `gh pr merge` — surface the command, let the user run it
- force-push anything
- commit to, or reset, the repository's default branch
- `git reset --hard`
- `git rebase`
- `git commit --amend` on a commit that has been pushed
- `git stash` — it would swallow an agent's uncommitted work
- `git commit --no-verify` — a pre-commit hook rejection is a finding to report,
  not an obstacle to route around
