# review

Comprehensive, language-agnostic PR review. One orchestrator skill coordinates a
change analysis, a 3-pass deep code review, security scanning,
documentation-drift checks, and code-fix generation — then
posts a single unified GitHub review (summary + inline comments). Rust and Machinify
`mac-ui` changes get first-class, tailored checks. Test execution and coverage
analysis are intentionally left to CI.

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
| `analyze` | Detects languages, frameworks, test setup, and impact/security sensitivity. |
| `security-scan` | Runs available static analyzers (semgrep, linters, dependency audits); degrades gracefully when tools aren't installed. |
| `docs-drift` | Detects docs (ADRs, OpenAPI, rendered artifacts, READMEs, comments) that have drifted out of sync with the changed code, plus doc-completeness gaps. |
| `codegen` | Drafts tests, docstrings, and CHANGELOG entries to fill surfaced gaps (human review required before committing). |
| `monitor-pr` | Continuously watches a PR (drive with `/loop`) for CI failures and new review comments, tracks findings in a scratch file, dispatches subagents to fix them (in parallel when independent), and resolves/acknowledges each comment once its fix is pushed. |

**Rust & mac-ui tailoring:** `analyze` detects Rust (cargo/just/nextest)
and `@vlognow/mac-ui` (Machinify Web Components) usage. When present, `security-scan`
and `docs-drift` adapt automatically — running cargo supply-chain tools
and Rust correctness/PHI checks, and fetching mac-ui's **live** authority docs
(`ai-behavior-spec`, `ai-code-audit`, `ai-testing-guide`, per-component `mac-*.md`)
at review time since the framework changes.

Each sub-skill can also be invoked standalone (e.g. `/review:security-scan <PR_URL>`).

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
  ├─ Phase 1  analyze  →  deep code review (3 parallel bug-finder passes, inline)
  ├─ Phase 2  security-scan · docs-drift               (parallel)
  ├─ Phase 3  codegen
  └─ Phase 4  synthesize → merge recommendation → post unified review
```

The deep code review is self-contained: the orchestrator spawns three independent
bug-finders (NPE/lifecycle tracing, resource leaks, security sinks, race conditions,
control-flow, architectural consistency) and merges their findings, flagging any issue
found by multiple passes as high-confidence.

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
- Cost: roughly ~$4–8 per PR (3-pass deep review + the analysis/generation skills).
