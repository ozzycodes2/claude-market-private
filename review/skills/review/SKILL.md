---
name: review
description: Orchestrates comprehensive PR review combining analysis, code review, security, documentation, and risk-gated quality-review passes. Use when you want a full automated review of a GitHub PR posted as a single unified comment.
allowed-tools: Bash Read Write Skill Task
disable-model-invocation: true
---

# Orchestrate Full PR Review

Master orchestrator. Runs comprehensive PR review by coordinating specialized skills. Produces single unified review comment with all findings and recommendations.

## Overview

Workflow:

**Phase 1: Foundation**
1. Analyze changes (languages, frameworks, impact, **risk_class**)
2. Deep code review (3-pass bug hunting — expanded concurrency) **in parallel with** risk-gated QR passes

**Phase 2: Quality Checks** (parallel)
3. Security scanning (OWASP deepen)
4. Documentation validation (incl. light DX fold)

**Phase 3: Generation**
5. Generate code/docs (simple fixes)

**Phase 4: Synthesis**
6. Combine all findings (bug-finder + QR passes + security + docs)
7. Determine merge recommendation (Clean Code blockers count as critical/high)
8. Post comprehensive review to PR

## Usage

```bash
# Invoke with PR URL
> /review:review https://github.com/org/repo/pull/123

# The skill will automatically:
# - Analyze the PR
# - Run applicable reviews
# - Post results to PR
```

## Step 1: Validate Environment

### 1.1 Check gh CLI

```bash
gh --version && gh auth status
```

If not authenticated:
```
Error: GitHub CLI not authenticated
Run: gh auth login
Or for enterprise: gh auth login --hostname <host>
```

### 1.2 Extract PR Number and Create Session Directory

```bash
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]' | cut -d'-' -f1)
OUTPUT_DIR="/tmp/pr-review-${PR_NUMBER}-${SESSION_ID}"
mkdir -p "$OUTPUT_DIR" && chmod 700 "$OUTPUT_DIR"
echo "Session output directory: $OUTPUT_DIR" >&2
```

If PR URL not found, ask user for it.

### 1.3 Locate this plugin's scripts

Steps 8.5 and 9 run bundled scripts. A bare relative path resolves against the
**reviewed repo's** working directory, not this plugin — the same trap called out
in Step 3.1 — so resolve the root once, here.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ ! -f "$PLUGIN_ROOT/scripts/review_formatter.py" ]; then
  PLUGIN_ROOT="$(cd "${CLAUDE_SKILL_DIR:-.}/../.." 2>/dev/null && pwd)"
fi
[ -f "$PLUGIN_ROOT/scripts/review_formatter.py" ] \
  || echo "WARN: plugin scripts not found; Glob for review_formatter.py" >&2
```

If both variables are unset, Glob for `**/scripts/review_formatter.py` and use
that file's parent-of-parent.

## Step 2: Run Change Analysis (Foundation)

```
Use Skill tool:
- skill: "review:analyze"
- args: "<PR_URL> <OUTPUT_DIR>"
```

**Wait for completion** and read analysis:
```bash
Read tool: $OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json
```

Store key findings:
- `primary_language`
- `security_sensitive`
- `impact_analysis`
- `risk_class` (array)

**If analysis fails:** continue with limited info; note in final review.

## Step 3: Deep Code Review + Risk-Gated QR Passes (parallel Tasks)

### 3.1 Three-pass bug-finder (always)

Spawn **3 independent bug-finders in parallel** with Task tool. Different models per pass — one model three times shares one set of blind spots, so a finding two models agree on is far stronger signal:

| Pass | `model` | Model ID | Role |
|------|---------|----------|------|
| 1 | `opus` | `claude-opus-4-8` | Deepest reasoning — subtle logic, races, security data-flow |
| 2 | `sonnet` | `claude-sonnet-5` | Strong, different family — diversifies findings |
| 3 | `haiku` | `claude-haiku-4-5` | Fast breadth — cheap third perspective |

Each:
- `subagent_type`: `general-purpose`
- `model`: from table. **Do not omit** — an omitted `model` inherits the session model, collapsing all three passes onto one.
- `description`: `Bug hunter pass [1 opus / 2 sonnet / 3 haiku]`
- `prompt`: Bug-Finder Prompt below, with the PR diff inserted as `{{DIFF}}` and the contents of `references/anti-patterns.md` as `{{ANTI_PATTERNS}}`.

Read `references/anti-patterns.md` yourself and paste it in. These are raw Task prompts, not skill invocations — the subagents run with the reviewed repo as their working directory and cannot resolve a path in this skill.

### Bug-Finder Prompt (all 3 passes)

```
You are a bug hunter. Find bugs that will crash production or create security vulnerabilities. Trace, don't scan.

## Anti-patterns
{{ANTI_PATTERNS}}

## Critical Checks
- **NPE / null-deref:** for every dereference, trace the variable's lifecycle (declared? assigned? set null in cleanup/error paths? nulled by another thread?). Show the full trace for each risk.
- **Resource leaks:** every opened resource (connection, stream, file, cursor) — is it closed on all paths, including exceptions?
- **Security:** trace every external input to dangerous sinks (SQL, HTML, shell, file paths, logs) without sanitization. Also flag hardcoded secrets, sensitive data in logs, missing auth checks.
- **Race conditions:** shared mutable state without synchronization; check-then-act gaps.
- **Concurrency (expanded):** deadlocks / lock ordering; TOCTOU (filesystem/authz); async cancellation / lost wakeups / unstructured concurrency; concurrent idempotency (handler unsafe under parallel retries; missing unique constraints); poison messages / missing DLQ isolation.
- **Control flow:** missing returns after cleanup/error handling, early exits that skip cleanup, unreachable code.
- **Architectural:** inconsistent patterns (mixing two APIs for one purpose), wrappers/utilities removed without justification.
- **Clean Code (blocking):** silent catch / swallowed errors, shared mutable globals, or craft issues that hit correctness/invariants — emit as critical/high, not nits, **regardless of module reach**. Blast radius sets critical-vs-high, not blocking-vs-not. Name the resolving refactoring (Fowler/Kerievsky) in `suggestion`. Style-only with no domain-language conflict → omit or nitpick.

## Output
Return a JSON array of findings, each: {"severity":"critical|high|medium","label":"issue|suggestion|nitpick|question|thought|praise","decoration":"blocking|non-blocking|if-minor","path":"exact/path","line":N,"title":"5-10 words","body":"explanation with lifecycle/data-flow trace","suggestion":"concrete fix"}.
- `severity`: `critical` (crashes/security), `high` (fix soon), `medium` (fix later).
- `label`/`decoration` optional — omit for severity defaults (`critical`/`high` → `issue (blocking)`, `medium` → `suggestion (non-blocking)`).
- `path`/`line` required when mapped to diff (`line` = NEW-file line); add `start_line` for a multi-line range. Omit both for general findings.
- Wrap code refs in backticks; keep `body` to 1–2 terse sentences.
- After the JSON, add a 1-2 sentence summary. Focus on crashes and vulnerabilities, not style.

## Code to Review
{{DIFF}}
```

**Merge (Step 6):** group by `path`+`line`; prepend "[Found by N/3 models]" when 2+ passes agree; take highest severity.

### 3.2 Risk-gated QR passes (parallel with bug-finder)

Read `shared/risk-class-routing.md`. From `risk_class`, decide which of these skills to run:

| Gate | Skill |
|---|---|
| `domain` ∈ risk_class | `review:domain-architecture` |
| `data` or `api` ∈ risk_class | `review:data-contracts` |
| `ops` or `concurrency` ∈ risk_class | `review:ops-reliability` |
| Large/mixed/CD/design signals | `review:change-evolution` |

For each selected skill, spawn a Task (prefer `sonnet` unless domain/architecture needs `opus`):

```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"   # use "opus" for domain-architecture when risk is high
- description: "QR pass <name>"
- prompt: |
    Invoke Skill "review:<name>" with args "<PR_URL> <OUTPUT_DIR>".
    Follow that skill exactly — it scopes its own anti-pattern slice.
    Write $OUTPUT_DIR/<name>-<PR_NUMBER>.json. Return a one-line finding-count summary.
```

These invoke the skill, so they resolve its references themselves — unlike the bug-finders, they need nothing inlined.

If `risk_class` is empty, skip QR passes (bug-finder still runs).

Do not dispatch yet — Step 4's Tasks go out in the same message.

## Step 4: Run Phase 2 Skills (Parallel)

### 4.1 Security Scanner (Sonnet subagent)

```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"
- description: "Security scan (sonnet)"
- prompt: |
    Invoke Skill "review:security-scan" with args "<PR_URL> <OUTPUT_DIR>".
    Deepen OWASP authz/IDOR, business-logic abuse, SSRF, PII-in-logs per that
    skill. Write security-scan-<PR_NUMBER>.json. One-line summary.
```

### 4.2 Documentation Validator (Haiku subagent)

```
Use Task tool:
- subagent_type: "general-purpose"
- model: "haiku"
- description: "Docs drift check (haiku)"
- prompt: |
    Invoke Skill "review:docs-drift" with args "<PR_URL> <OUTPUT_DIR>".
    Include light DX fold (ADR/runbook/caller migration) per that skill.
    Write docs-drift-<PR_NUMBER>.json. One-line summary.
```

**Send every Step 3 and Step 4 Task in ONE message** — 3 bug-finders, 0–4 QR passes, security-scan, docs-drift. They are independent and all read the same analysis JSON. Continue to Step 5 without waiting; collect in Step 6.

## Step 5: Phase 3 - Code Generation

```
Use Skill tool:
- skill: "review:codegen"
- args: "<PR_URL> <OUTPUT_DIR>"
```

Wait and read `$OUTPUT_DIR/code-generation-<PR_NUMBER>.json`. Generated code is for review only — never auto-committed.

## Step 6: Collect Results

Wait for: bug-finder ×3, QR passes (if any), security-scan, docs-drift, codegen.

Parse:
- `$OUTPUT_DIR/pr-analysis-*.json` — risk_class
- Bug-finder merged findings
- `$OUTPUT_DIR/domain-architecture-*.json`, `data-contracts-*.json`, `ops-reliability-*.json`, `change-evolution-*.json` — each `findings` array
- `$OUTPUT_DIR/security-scan-*.json`
- `$OUTPUT_DIR/docs-drift-*.json`
- `$OUTPUT_DIR/code-generation-*.json`

The three bug-finders return their findings in context, not on disk. **Write the
merged array to `$OUTPUT_DIR/bug-finder-<PR_NUMBER>.json`** as
`{"findings": [...]}` — Step 8.5 collects the ledger from these files, and a pass
with no file on disk is a pass whose findings `/review:fix` will never see.

## Step 7: Determine Merge Recommendation

```
IF (any finding carries decoration "blocking"):
  RECOMMENDATION = "REQUEST CHANGES"
  RATIONALE = "<N> blocking findings — <top 3 titles by priority stack>"

ELIF (missing_critical_docs) OR (security_sensitive === true):
  RECOMMENDATION = "COMMENT"
  RATIONALE = "Non-blocking findings; manual review required"

ELSE:
  RECOMMENDATION = "COMMENT"
  RATIONALE = "Review completed - findings noted for consideration"
```

A finding decorated `(blocking)` that yields a `COMMENT` verdict teaches the
author to ignore the decoration. One blocking finding is enough for
`REQUEST CHANGES`; counts and severity tiers only order the output.

Always default to COMMENT (never APPROVE) — human-in-the-loop.

## Step 8: Build structured JSON for shared formatter

### Sections

1. **Change Analysis** — body: languages, impact, `risk_class`. No inline findings.
2. **Code Review Results (3 Passes)** — bug-finder findings (inline when path+line).
3. **Domain & Architecture** — from `domain-architecture` (omit if skipped/empty).
4. **Data & Contracts** — from `data-contracts` (omit if skipped/empty).
5. **Ops & Reliability** — from `ops-reliability` (omit if skipped/empty).
6. **Change & Evolution** — from `change-evolution` (omit if skipped/empty).
7. **Security Analysis** — security-scan findings.
8. **Documentation Check** — docs-drift body (+ inline if path+line).
9. **Code Generation** — codegen body.

Set `review_metadata.model` to your model ID. Note bug-finder pass models in Code Review body. Set `tool_version` from `.claude-plugin/plugin.json` (do not hardcode).

### Conventional Comments

Formatter applies `<label> [decoration]: <subject>`. Finding fields match bug-finder schema. Severity defaults per `shared/severity-rubric.md`. **Clean Code and category 4 design quality → blocking regardless of module reach.**

### Formatting rules

- Code refs in backticks; bullets not paragraphs; lead with takeaway.

### Ordering `required_actions`

Blocking design and craft dimensions mean most non-trivial PRs return
`REQUEST CHANGES`. Order `required_actions` by the taxonomy priority stack
(`shared/quality-review-pr-review-taxonomy.md`, "QR / Staff-style priority
stack"): intent → system fit → domain invariants → failure behavior →
contracts → test adequacy → design simplicity → security → maintainability →
craft.

**List every blocking finding. Do not cap, summarize, or elide.** The consumer
may be an agent working the list to completion, so an omitted action is an
unfixed finding. Ordering sets the sequence; it never sets the membership.

Each entry must be actionable on its own, without reading the rest of the
review: name the path (and line, when mapped), the symptom, and the fix. For a
craft or design finding, name the resolving refactoring.

### Build JSON

```json
{
  "pr_url": "<FULL_PR_URL>",
  "recommendation": "<REQUEST_CHANGES|COMMENT>",
  "rationale": "<Brief summary from Step 7>",
  "required_actions": ["<action1>"],
  "optional_improvements": ["<suggestion1>"],
  "sections": [
    {"title": "Change Analysis", "summary_line": "...", "body": "..."},
    {"title": "Code Review Results (3 Passes)", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Domain & Architecture", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Data & Contracts", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Ops & Reliability", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Change & Evolution", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Security Analysis", "summary_line": "...", "body": "...", "findings": []},
    {"title": "Documentation Check", "summary_line": "...", "body": "..."},
    {"title": "Code Generation", "summary_line": "...", "body": "..."}
  ],
  "review_metadata": {
    "tool_name": "review",
    "review_title": "Review",
    "tool_version": "<from plugin.json>",
    "model": "<orchestrator model ID>"
  }
}
```

Omit skipped/failed/empty QR sections. Formatter omits empty sections.

**Write this JSON to `$OUTPUT_DIR/review-payload.json`** — Steps 8.5 and 9 both
read it from there.

## Step 8.5: Persist findings to the durable ledger

Steps 1-8 wrote everything to `$OUTPUT_DIR`, which is a `/tmp` dir keyed on a
random session id. A later session cannot find it, so the findings — and the
refactorings they name — die with this run. Write them somewhere durable instead,
so `/review:fix` can work the list to completion.

```bash
LEDGER=$(python3 "$PLUGIN_ROOT/scripts/findings_ledger.py" build \
  --pr-url "$PR_URL" \
  --analysis "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" \
  --payload  "$OUTPUT_DIR/review-payload.json" \
  --run "$SESSION_ID" \
  $(for f in "$OUTPUT_DIR"/*-${PR_NUMBER}.json; do
      case "$(basename "$f")" in
        pr-analysis-*|code-generation-*) continue ;;
      esac
      printf ' --source %s=%s' "$(basename "$f" | sed "s/-${PR_NUMBER}\.json$//")" "$f"
    done) \
  | cut -f1)
```

The script derives `~/.claude/review-findings/<owner>__<repo>/pr-<N>.json` from
the PR URL, normalizes all four finding shapes into one schema, and copies the
`test_setup` / `build_system` / `languages` slice of the analysis into the ledger.
That slice is copied rather than referenced because `$OUTPUT_DIR` is gone by the
time `fix` runs.

The ledger holds source excerpts from security findings, so the script writes it
`0600` under a `0700` directory and replaces any reported credential with a
digest. Do not copy ledger contents into a log line or a PR comment.

If this step fails, the review is still complete — report the failure and move
on. The ledger is an optimization for `fix`, not part of the review verdict.

## Step 9: Post review via shared formatter

```bash
cat "$OUTPUT_DIR/review-payload.json" \
  | python3 "$PLUGIN_ROOT/scripts/review_formatter.py" --post
```

On failure, `--dry-run` and show the user.

## Step 10: Provide User Summary

```
Comprehensive Review Complete

Summary:
- Languages: <primary>
- Risk classes: <list or none>
- Code Review: <X Critical, Y High, Z Medium>
- QR passes: <which ran>
- Security: <counts>
- Documentation: <status>
- Recommendation: <REQUEST CHANGES | COMMENT>

View full review: <PR_URL>
```

## Error Handling

- analyze fails → continue; omit Change Analysis; note in rationale
- bug-finder fails → omit Code Review section; recommend manual review
- a QR pass fails → omit that section; continue
- both analyze and bug-finder fail → do not post incomplete review
- post fails → dry-run + save JSON under `$OUTPUT_DIR`

## Notes

- Entry point for comprehensive reviews
- Model-diverse 3-pass bug-finder (opus+sonnet+haiku) + risk-gated QR skills (`domain-architecture`, `data-contracts`, `ops-reliability`, `change-evolution`) + security-scan + docs-drift + codegen
- Each pass owns its anti-pattern slice at `skills/<pass>/references/anti-patterns.md`, so it can address no other
- Clean Code and category 4 design-quality findings are **blockers regardless of module reach**; blast radius sets severity only. Each names its resolving refactoring
- Test execution/coverage left to CI
- Never auto-approves/merges
- Cost: higher when QR passes gate on; still prefer gated runs over always-on four extras
