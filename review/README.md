# review

Comprehensive, language-agnostic PR review. One orchestrator skill coordinates a
change analysis (with **risk_class** routing), a 3-pass deep
code review (expanded concurrency), risk-gated quality-review passes
(`domain-architecture`, `data-contracts`, `ops-reliability`, `change-evolution`),
security scanning (OWASP deepen), documentation-drift checks (light DX fold), and
code-fix generation — then posts a single unified GitHub review (summary +
inline comments). Rust and Machinify `mac-ui` changes get first-class, tailored
checks. Test execution and coverage analysis are intentionally left to CI.

## Usage

```
> review this PR: https://github.com/org/repo/pull/123
```

Or invoke the orchestrator explicitly:

```
/review:review https://github.com/org/repo/pull/123
```

The orchestrator runs the full workflow and posts one consolidated review to the PR
(it never auto-approves — the recommendation is always `COMMENT` or `REQUEST_CHANGES`,
keeping a human in the loop).

## Skills

| Skill | What it does |
|-------|--------------|
| `review` | Orchestrator — runs all phases and posts the unified review. |
| `analyze` | Detects languages, frameworks, test setup, impact/security sensitivity, and **`risk_class`**. |
| `domain-architecture` | QR pass — domain model, architecture dependency rules, team/org boundaries (taxonomy categories 1 Domain, 2 Architecture, 15 Team / org boundaries). Risk-gated on `domain`. |
| `data-contracts` | QR pass — data consistency + API/event contracts (categories 7 Data & consistency, 11 API / contract design). Risk-gated on `data` / `api`. |
| `ops-reliability` | QR pass — reliability, performance, concurrency leftovers (categories 8 Reliability & operability, 10 Performance & scalability, plus concurrency leftovers). Risk-gated on `ops` / `concurrency`. |
| `change-evolution` | QR pass — CD readiness + design quality YAGNI/deep modules (categories 5 Change & evolution, 4 Design quality). Gated on size/mixed/CD/design. |
| `security-scan` | Runs available static analyzers; deepens OWASP authz/IDOR, business-logic abuse, SSRF, PII-in-logs; degrades gracefully when tools aren't installed. |
| `docs-drift` | Detects docs drift (ADRs, OpenAPI, rendered artifacts, READMEs, comments) plus light DX fold (runbooks / caller migration) and completeness gaps. |
| `codegen` | Drafts tests, docstrings, and CHANGELOG entries to fill surfaced gaps (human review required before committing). |
| `fix` | Applies the recorded findings — refactors each smell by its named Fowler/Kerievsky move in the language's own idiom, rewrites flagged docs and comments, regenerates stale artifacts, defers design decisions. One commit per finding, then replies to and resolves the review comments that raised them; **never pushes**. |
| `monitor-pr` | Continuously watches a PR (drive with `/loop`) for CI failures and new review comments, appends them to the findings ledger, delegates every edit to `fix`, pushes, and resolves/acknowledges each comment once its fix is pushed. |

**Anti-patterns:** each pass owns its slice at
`skills/<pass>/references/anti-patterns.md`, so it can address no other. Shared
severity and routing live in `shared/severity-rubric.md` and
`shared/risk-class-routing.md`. Taxonomy source:
`shared/quality-review-pr-review-taxonomy.md`.

**Clean Code & design quality:** craft issues that hit correctness, invariants,
or maintainability are **blockers**, not deferred to nits — and not exempted by
module reach. Blast radius sets `critical` vs `high`, not blocking vs not. Each
finding names the refactoring that resolves it (Fowler, *Refactoring*;
Kerievsky, *Refactoring to Patterns*), using the language's idiom where it
diverges from the catalog's OO move.

**Rust & mac-ui tailoring:** `analyze` detects Rust (cargo/just/nextest)
and `@vlognow/mac-ui` (Machinify Web Components) usage. When present, `security-scan`
and `docs-drift` adapt automatically — running cargo supply-chain tools
and Rust correctness/PHI checks, and fetching mac-ui's **live** authority docs
(`ai-behavior-spec`, `ai-code-audit`, `ai-testing-guide`, per-component `mac-*.md`)
at review time since the framework changes.

Each sub-skill can also be invoked standalone (e.g. `/review:security-scan <PR_URL>`,
`/review:domain-architecture <PR_URL>`).

## Fix the findings

`review` diagnoses; `fix` resolves. Every finding names the refactoring that
resolves it, and `fix` is the consumer that list was written for:

```
/review:fix 123
/review:fix https://github.com/org/repo/pull/123 --dry-run
```

It reads the findings ledger `review` wrote, routes each finding to one strategy —
refactor, repair, prose, comment, regenerate, formatter, or honest deferral — and
makes **one commit per finding** in the working tree. There is no `--only` and no
`--severity`: the scope is every open finding.

Then it answers the review. `review` raised each finding as an inline comment, so
`fix` replies to that comment with what changed and the sha, and resolves the
thread. A **deferred** finding gets a reply stating the decision it needs and the
thread stays open — it is the one finding that most needs a human to see it.

A thread is resolved only once its commit is on the remote, which `fix` never
pushes to. So the usual sequence is:

```
/review:fix 123                 # fixes, commits, pushes nothing
git push                        # your call
/review:fix 123 --ack-only      # answers and resolves the threads
```

The report names the unacknowledged findings and that last command, so it is not
something you have to remember. `--no-ack` skips GitHub entirely.

What it will not do:

- **It never pushes, merges, or force-pushes.** The commits sit on your branch,
  ahead of the remote, for you to review.
- **It never resolves a thread it cannot back.** Not a deferral, not a thread
  this run did not fix, and not a commit that exists only on your machine.
  Acknowledgements are recorded in the ledger, so no reviewer is answered twice —
  even when `monitor-pr` is driving.
- **It never commits a red suite.** It establishes a green baseline first (you
  cannot refactor on red), then iterates on each change until the tests pass. A
  failing test is not a reason to revert or defer.
- **It never guesses a design.** A finding with two defensible answers —
  outbox table vs. CDC vs. accept the window — is deferred with the question
  stated, not half-implemented and not left as a bare `TODO`.
- **It never hand-edits a generated artifact.** Those are regenerated by the
  repo's own command, or deferred when no command can be found.

Refactorings come from Fowler's *Refactoring* and Kerievsky's *Refactoring to
Patterns*, applied in the language's idiom where the two diverge — in Rust a
string-typed state becomes an `enum` with exhaustive `match`, not a trait
hierarchy. Prose follows Zinsser's *On Writing Well*, reaching no further than
the flagged line and its paragraph, and preserving the claim the passage made.

### The findings ledger

```
~/.claude/review-findings/<owner>__<repo>/pr-<n>.json
```

`review` writes it, `fix` consumes it, `monitor-pr` appends to it. It lives
outside every repository, so it survives compaction, `git clean`, and worktree
switches — which is what makes `fix` resumable and lets a killed run pick up
without double-committing.

**It may contain source excerpts from the repository under review.** A security
finding quotes the offending line, so the directory is created mode `700` and
each file mode `600`. Secret *values* are never stored — a hardcoded-credential
finding keeps a `sha256:` fingerprint, enough to tell two findings apart and not
enough to use. Nothing is written to it that a reviewer could not already read in
the diff.

## Monitor a PR (post-open)

Where `review` *produces* a review, `monitor-pr` *reacts* to what lands on a PR you
opened — CI failures and incoming review comments — and shepherds it to green:

```
> /monitor-pr 45
> watch PR #45 for comments and check failures and fix them as they come
> /monitor-pr 45 --critical-only        # act only on CI failures + blocking bot threads
```

It baselines the PR, then on each `/loop` tick polls CI + review threads
(`skills/monitor-pr/scripts/poll-pr.sh`, read-only), appends what it found to the
findings ledger, and
calls `/review:fix` to do the editing. **It edits nothing itself** — the division is
`monitor-pr` polls and pushes, `fix` fixes. CI failures and the bot's own review
threads are handled automatically; human comments and nits are reported for your
decision and never reach `fix` until you agree.

`fix` commits but does not push, so `monitor-pr` pushes the branch afterwards and
then acknowledges: **every comment whose fix ships gets answered** — the review
thread is resolved, or, if it isn't inline/resolvable, a new comment replies
`@author` with the sha. `.claude/pr-monitor/pr-<n>.md` is a human-readable mirror of
the ledger, deleted once everything is handled and CI is green; the ledger stays as
the record. It never merges or force-pushes — that stays with you.

## How it works

```
/review:review <PR_URL>
  │
  ├─ Phase 1  analyze → risk_class
  │            ├─ 3-pass bug-finder (parallel, model-diverse)
  │            └─ QR passes gated by risk_class (parallel Task)
  ├─ Phase 2  security-scan · docs-drift               (parallel)
  ├─ Phase 3  codegen
  └─ Phase 4  synthesize → merge recommendation → post unified review
              └─ write the findings ledger

/review:fix [<PR>]            reads the ledger → routes → commits one per finding
                              → replies to and resolves the threads it answered
/monitor-pr <PR>              polls → appends to the ledger → calls fix → pushes
                              → acknowledges what the push made visible
```

The deep code review is self-contained: the orchestrator spawns three independent
bug-finders (NPE/lifecycle tracing, resource leaks, security sinks, races,
deadlocks, TOCTOU, async cancellation, concurrent idempotency, DLQ/poison,
control-flow, architectural consistency) and merges their findings, flagging any
issue found by multiple passes as high-confidence.

## Requirements

- **`gh` CLI**, authenticated (`gh auth status`) — all PR data comes from `gh pr`.
- **Python 3.14+** — the review formatter (`scripts/review_formatter.py`, standard
  library only) builds and posts the structured GitHub review.
- Optional: `semgrep`, language linters, and dependency-audit tools for richer
  `security-scan` results (it degrades gracefully without them).

## Notes

- Generated code (from `codegen`) is for review only — never auto-committed. Its
  drafted lint diffs are evidence that drift exists; `fix` discards them and runs
  the repo's own formatter, which is authoritative.
- `fix` is the only skill in the plugin that writes to the repository, and it is
  `disable-model-invocation` — it fires only when you ask for it by name, or when
  `monitor-pr` delegates to it.
- Test execution and coverage/test-gap analysis are intentionally out of scope —
  CI already runs the suite and measures coverage, so the review doesn't duplicate it.
- Cost: roughly ~$4–10 per PR depending on how many QR passes gate on
  (3-pass deep review + analysis/generation + zero-to-four QR skills).
