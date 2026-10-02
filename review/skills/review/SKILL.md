---
name: review
description: Orchestrates comprehensive PR review combining analysis, code review, security, documentation, and risk-gated principal-engineer passes. Use when you want a full automated review of a GitHub PR posted as a single unified comment.
allowed-tools: Bash Read Write Skill Task
disable-model-invocation: true
---

# Orchestrate Full PR Review

Master orchestrator. Runs comprehensive PR review by coordinating specialized skills. Produces single unified review comment with all findings and recommendations.

## Overview

Workflow:

**Phase 1: Foundation**
1. Analyze changes (languages, frameworks, impact, **risk_class**, hygiene preflight)
2. Deep code review (3-pass bug hunting — expanded concurrency) **in parallel with** risk-gated PE passes

**Phase 2: Quality Checks** (parallel)
3. Security scanning (OWASP deepen; reads only `anti-patterns/security-scan.md`)
4. Documentation validation (incl. light DX fold)

**Phase 3: Generation**
5. Generate code/docs (simple fixes)

**Phase 4: Synthesis**
6. Combine all findings (bug-finder + PE passes + security + docs)
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
- `hygiene` (size / one_concern / description_map)

**If analysis fails:** continue with limited info; note in final review.

## Step 3: Deep Code Review + Risk-Gated PE Passes (parallel Tasks)

### 3.1 Three-pass bug-finder (always)

Spawn **3 independent bug-finders in parallel** with Task tool. Different models per pass:

| Pass | `model` | Role |
|------|---------|------|
| 1 | `opus` | Deepest reasoning — subtle logic, races, security data-flow |
| 2 | `sonnet` | Strong, diversifies findings |
| 3 | `haiku` | Fast breadth — cheap third perspective |

**Send ONE message with THREE Task tool calls.** Each:
- `subagent_type`: `general-purpose`
- `model`: from table (**do not omit**)
- `description`: `Bug hunter pass [1 opus / 2 sonnet / 3 haiku]`
- `prompt`: Bug-Finder Prompt below, with PR diff inserted as `{{DIFF}}`.

Each bug-finder pass must **read only** `references/anti-patterns/bug-finder.md` (do not load other anti-pattern files).

### Bug-Finder Prompt (all 3 passes)

```
You are a bug hunter. Find bugs that will crash production or create security vulnerabilities. Trace, don't scan.

Before reviewing, read ONLY references/anti-patterns/bug-finder.md (no other anti-pattern files).

## Critical Checks
- **NPE / null-deref:** for every dereference, trace the variable's lifecycle (declared? assigned? set null in cleanup/error paths? nulled by another thread?). Show the full trace for each risk.
- **Resource leaks:** every opened resource (connection, stream, file, cursor) — is it closed on all paths, including exceptions?
- **Security:** trace every external input to dangerous sinks (SQL, HTML, shell, file paths, logs) without sanitization. Also flag hardcoded secrets, sensitive data in logs, missing auth checks.
- **Race conditions:** shared mutable state without synchronization; check-then-act gaps.
- **Concurrency (expanded):** deadlocks / lock ordering; TOCTOU (filesystem/authz); async cancellation / lost wakeups / unstructured concurrency; concurrent idempotency (handler unsafe under parallel retries; missing unique constraints); poison messages / missing DLQ isolation.
- **Control flow:** missing returns after cleanup/error handling, early exits that skip cleanup, unreachable code.
- **Architectural:** inconsistent patterns (mixing two APIs for one purpose), wrappers/utilities removed without justification.
- **Clean Code (blocking):** silent catch / swallowed errors, shared mutable globals, or craft issues that hit correctness/invariants on shared/hot paths — emit as critical/high, not nits. Style-only → omit or nitpick.

## Output
Return a JSON array of findings, each: {"severity":"critical|high|medium","label":"issue|suggestion|nitpick|question|thought|praise","decoration":"blocking|non-blocking|if-minor","path":"exact/path","line":N,"title":"5-10 words","body":"explanation with lifecycle/data-flow trace","suggestion":"concrete fix"}.
- `severity`: `critical` (crashes/security), `high` (fix soon), `medium` (fix later).
- `label`/`decoration` optional — omit for severity defaults (`critical`/`high` → `issue (blocking)`, `medium` → `suggestion (non-blocking)`).
- `path`/`line` required when mapped to diff (`line` = NEW-file line); omit for general findings.
- Wrap code refs in backticks; keep `body` to 1–2 terse sentences.
- After the JSON, add a 1-2 sentence summary. Focus on crashes and vulnerabilities, not style.

## Code to Review
{{DIFF}}
```

**Merge (Step 6):** group by `path`+`line`; prepend "[Found by N/3 models]" when 2+ passes agree; take highest severity.

### 3.2 Risk-gated PE passes (parallel with bug-finder)

Read `references/risk-class-routing.md`. From `risk_class` + `hygiene`, decide which of these skills to run:

| Gate | Skill |
|---|---|
| `domain` ∈ risk_class | `review:domain-architecture` |
| `data` or `api` ∈ risk_class | `review:data-contracts` |
| `ops` or `concurrency` ∈ risk_class | `review:ops-reliability` |
| Large/mixed/CD/design signals **or** hygiene flags (unreviewable size, !one_concern, weak description_map) | `review:change-evolution` |

For each selected skill, spawn a Task (prefer `sonnet` unless domain/architecture needs `opus`):

```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"   # use "opus" for domain-architecture when risk is high
- description: "PE pass <name>"
- prompt: |
    Invoke Skill "review:<name>" with args "<PR_URL> <OUTPUT_DIR>".
    Follow that skill exactly. It must read ONLY
    references/anti-patterns/<name>.md (no other anti-pattern files).
    Write $OUTPUT_DIR/<name>-<PR_NUMBER>.json. Return a one-line finding-count summary.
```

**Send bug-finder Tasks + PE Tasks in as few messages as possible** so they run concurrently. Do not wait yet — collect in Step 6.

If `risk_class` is empty and hygiene is clean, skip PE passes (bug-finder still runs).

## Step 4: Run Phase 2 Skills (Parallel)

### 4.1 Security Scanner (Sonnet subagent)

```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"
- description: "Security scan (sonnet)"
- prompt: |
    Invoke Skill "review:security-scan" with args "<PR_URL> <OUTPUT_DIR>".
    Read ONLY references/anti-patterns/security-scan.md for anti-patterns
    (plus the skill's own references/*). Deepen OWASP authz/IDOR, business-logic
    abuse, SSRF, PII-in-logs. Write security-scan-<PR_NUMBER>.json. One-line summary.
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

Send both Task calls in ONE message. Continue to Step 5; collect in Step 6.

## Step 5: Phase 3 - Code Generation

```
Use Skill tool:
- skill: "review:codegen"
- args: "<PR_URL> <OUTPUT_DIR>"
```

Wait and read `$OUTPUT_DIR/code-generation-<PR_NUMBER>.json`. Generated code is for review only — never auto-committed.

## Step 6: Collect Results

Wait for: bug-finder ×3, PE passes (if any), security-scan, docs-drift, codegen.

Parse:
- `$OUTPUT_DIR/pr-analysis-*.json` — risk_class, hygiene
- Bug-finder merged findings
- `$OUTPUT_DIR/domain-architecture-*.json`, `data-contracts-*.json`, `ops-reliability-*.json`, `change-evolution-*.json` — each `findings` array
- `$OUTPUT_DIR/security-scan-*.json`
- `$OUTPUT_DIR/docs-drift-*.json`
- `$OUTPUT_DIR/code-generation-*.json`

## Step 7: Determine Merge Recommendation

```
IF (Critical code/PE/security findings > 0) OR (Clean Code blockers on correctness/invariants/hot paths):
  RECOMMENDATION = "REQUEST CHANGES"

ELIF (High findings > 3) OR (security_sensitive AND high_security_findings > 0):
  RECOMMENDATION = "REQUEST CHANGES"

ELIF (High findings > 0) OR (missing_critical_docs) OR (hygiene.unreviewable):
  RECOMMENDATION = "COMMENT"

ELIF (security_sensitive === true):
  RECOMMENDATION = "COMMENT"

ELSE:
  RECOMMENDATION = "COMMENT"
```

Always default to COMMENT (never APPROVE) — human-in-the-loop.

## Step 8: Build structured JSON for shared formatter

### Sections

1. **Change Analysis** — body: languages, impact, `risk_class`, hygiene summary. No inline findings.
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

Formatter applies `<label> [decoration]: <subject>`. Finding fields match bug-finder schema. Severity defaults per `references/severity-rubric.md`. **Clean Code on correctness/invariants/shared hot paths → blocking.**

### Formatting rules

- Code refs in backticks; bullets not paragraphs; lead with takeaway.

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
    "model": "<orchestrator model ID>",
    "stages": ["Change Analysis", "Code Review", "PE Passes", "Security", "Documentation", "Code Generation"]
  }
}
```

Omit skipped/failed/empty PE sections. Formatter omits empty sections.

## Step 9: Post review via shared formatter

```bash
cat "$OUTPUT_DIR/review-payload.json" | python3 scripts/review_formatter.py --post
```

On failure, `--dry-run` and show the user.

## Step 10: Provide User Summary

```
Comprehensive Review Complete

Summary:
- Languages: <primary>
- Risk classes: <list or none>
- Code Review: <X Critical, Y High, Z Medium>
- PE passes: <which ran>
- Security: <counts>
- Documentation: <status>
- Recommendation: <REQUEST CHANGES | COMMENT>

View full review: <PR_URL>
```

## Error Handling

- analyze fails → continue; omit Change Analysis; note in rationale
- bug-finder fails → omit Code Review section; recommend manual review
- a PE pass fails → omit that section; continue
- both analyze and bug-finder fail → do not post incomplete review
- post fails → dry-run + save JSON under `$OUTPUT_DIR`

## Notes

- Entry point for comprehensive reviews
- Model-diverse 3-pass bug-finder (opus+sonnet+haiku) + risk-gated PE skills (`domain-architecture`, `data-contracts`, `ops-reliability`, `change-evolution`) + security-scan + docs-drift + codegen
- Each pass reads **only** its matching `references/anti-patterns/<name>.md`
- Clean Code craft issues that hit correctness/invariants/shared hot paths are **blockers**, not nits
- Test execution/coverage left to CI
- Never auto-approves/merges
- Cost: higher when PE passes gate on; still prefer gated runs over always-on four extras
