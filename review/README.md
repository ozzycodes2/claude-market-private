# review

Comprehensive, language-agnostic PR review. One orchestrator skill coordinates a
change analysis (with **risk_class** routing + light PR hygiene), a 3-pass deep
code review (expanded concurrency), risk-gated principal-engineer passes
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
| `analyze` | Detects languages, frameworks, test setup, impact/security sensitivity, **`risk_class`**, and light PR hygiene (size / one-concern / description map). |
| `domain-architecture` | PE pass — domain model, architecture dependency rules, team/org boundaries (taxonomy cats 1, 2, 15). Risk-gated on `domain`. |
| `data-contracts` | PE pass — data consistency + API/event contracts (cats 7, 11). Risk-gated on `data` / `api`. |
| `ops-reliability` | PE pass — reliability, performance, concurrency leftovers (cats 8, 10 + leftovers). Risk-gated on `ops` / `concurrency`. |
| `change-evolution` | PE pass — CD readiness + design quality YAGNI/deep modules (cats 5, 4). Gated on size/mixed/CD/design or hygiene flags. |
| `security-scan` | Runs available static analyzers; deepens OWASP authz/IDOR, business-logic abuse, SSRF, PII-in-logs; degrades gracefully when tools aren't installed. |
| `docs-drift` | Detects docs drift (ADRs, OpenAPI, rendered artifacts, READMEs, comments) plus light DX fold (runbooks / caller migration) and completeness gaps. |
| `codegen` | Drafts tests, docstrings, and CHANGELOG entries to fill surfaced gaps (human review required before committing). |
| `monitor-pr` | Continuously watches a PR (drive with `/loop`) for CI failures and new review comments, tracks findings in a scratch file, dispatches subagents to fix them (in parallel when independent), and resolves/acknowledges each comment once its fix is pushed. |

**Anti-patterns:** each pass reads **only** its matching slice under
`references/anti-patterns/` (never one shared dump). Shared severity and
routing live in `references/severity-rubric.md` and
`references/risk-class-routing.md`. Taxonomy source:
`references/principal-engineer-pr-review-taxonomy.md`.

**Clean Code:** craft issues that hit correctness, invariants, or maintainability
on shared/hot paths are **blockers**, not deferred to nits.

**Rust & mac-ui tailoring:** `analyze` detects Rust (cargo/just/nextest)
and `@vlognow/mac-ui` (Machinify Web Components) usage. When present, `security-scan`
and `docs-drift` adapt automatically — running cargo supply-chain tools
and Rust correctness/PHI checks, and fetching mac-ui's **live** authority docs
(`ai-behavior-spec`, `ai-code-audit`, `ai-testing-guide`, per-component `mac-*.md`)
at review time since the framework changes.

Each sub-skill can also be invoked standalone (e.g. `/review:security-scan <PR_URL>`,
`/review:domain-architecture <PR_URL>`).

## Monitor a PR (post-open)

Where `review` *produces* a review, `monitor-pr` *reacts* to what lands on a PR you
opened — CI failures and incoming review comments — and shepherds it to green:

```
> /monitor-pr 45
> watch PR #45 for comments and check failures and fix them as they come
> /monitor-pr 45 --critical-only        # act only on CI failures + blocking bot threads
```

It baselines the PR, then on each `/loop` tick polls CI + review threads
(`scripts/poll-pr.sh`, read-only), records findings in `.claude/pr-monitor/pr-<n>.md`,
and dispatches subagents to fix — in parallel when the work is independent. CI failures
and the bot's own review threads are fixed automatically; human comments and nits are
reported for your decision. **When a fix is pushed, the corresponding comment is always
acknowledged** — the review thread is resolved, or, if it isn't inline/resolvable, a new
comment replies `@author` with the fix. The tracker is deleted once everything is
handled and CI is green. It never merges or force-pushes — that stays with you.

## How it works

```
/review:review <PR_URL>
  │
  ├─ Phase 1  analyze → risk_class + hygiene
  │            ├─ 3-pass bug-finder (parallel, model-diverse)
  │            └─ PE passes gated by risk_class / hygiene (parallel Task)
  ├─ Phase 2  security-scan · docs-drift               (parallel)
  ├─ Phase 3  codegen
  └─ Phase 4  synthesize → merge recommendation → post unified review
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

- Generated code (from `codegen`) is for review only — never auto-committed.
- Test execution and coverage/test-gap analysis are intentionally out of scope —
  CI already runs the suite and measures coverage, so the review doesn't duplicate it.
- Cost: roughly ~$4–10 per PR depending on how many PE passes gate on
  (3-pass deep review + analysis/generation + zero-to-four PE skills).
