# comprehensive-pr-review

Comprehensive, language-agnostic PR review. One orchestrator skill coordinates a
change analysis, a 3-pass deep code review, security scanning, test-gap analysis,
documentation-drift checks, optional test execution, and code-fix generation — then
posts a single unified GitHub review (summary + inline comments). Rust and Machinify
`mac-ui` changes get first-class, tailored checks.

## Usage

```
> review this PR: https://github.com/org/repo/pull/123
```

Or invoke the orchestrator explicitly:

```
/comprehensive-pr-review:review https://github.com/org/repo/pull/123
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
| `test-gaps` | Assesses coverage and recommends new tests for the change. |
| `docs-drift` | Detects docs (ADRs, OpenAPI, rendered artifacts, READMEs, comments) that have drifted out of sync with the changed code, plus doc-completeness gaps. |
| `run-tests` | Executes the suite in a sandboxed, timeout-limited way — only when analysis deems it safe. |
| `codegen` | Drafts tests, docstrings, and CHANGELOG entries to fill surfaced gaps (human review required before committing). |

**Rust & mac-ui tailoring:** `analyze` detects Rust (cargo/just/nextest/llvm-cov)
and `@vlognow/mac-ui` (Machinify Web Components) usage. When present, `security-scan`,
`test-gaps`, and `docs-drift` adapt automatically — running cargo supply-chain tools
and Rust correctness/PHI checks, mapping Rust's in-file tests to real `llvm-cov`
coverage, and fetching mac-ui's **live** authority docs (`ai-behavior-spec`,
`ai-code-audit`, `ai-testing-guide`, per-component `mac-*.md`) at review time since
the framework changes.

Each sub-skill can also be invoked standalone (e.g. `/comprehensive-pr-review:security-scan <PR_URL>`).

## How it works

```
/comprehensive-pr-review:review <PR_URL>
  │
  ├─ Phase 1  analyze  →  deep code review (3 parallel bug-finder passes, inline)
  ├─ Phase 2  test-gaps · security-scan · docs-drift   (parallel)
  ├─ Phase 3  run-tests (if safe) · codegen            (conditional)
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
- `run-tests` executes repository code; it only runs when `analyze` marks the setup
  safe, otherwise it falls back to recommending a manual command.
- Cost: roughly ~$5–10 per PR (3-pass deep review + the analysis/execution skills).
