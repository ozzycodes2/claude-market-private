---
name: review
description: Orchestrates comprehensive PR review combining analysis, code review, testing, security, and documentation checks. Use when you want a full automated review of a GitHub PR posted as a single unified comment.
allowed-tools: Bash Read Skill Task
---

# Orchestrate Full PR Review

Master orchestrator that runs a comprehensive PR review by coordinating multiple specialized skills. Produces a single unified review comment with all findings and recommendations.

## Overview

This skill coordinates the full review workflow:

**Phase 1: Foundation**
1. Analyze changes (detect languages, frameworks, impact)
2. Deep code review (3-pass bug hunting)

**Phase 2: Quality Checks** (parallel)
3. Test analysis (coverage, recommendations)
4. Security scanning
5. Documentation validation

**Phase 3: Execution** (conditional)
6. Run tests (if safe)
7. Generate code/docs (simple fixes)

**Phase 4: Synthesis**
8. Combine all findings
9. Determine merge recommendation
10. Post comprehensive review to PR

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

Extract PR number from URL:
```bash
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
```

Create unique output directory for this session:
```bash
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]' | cut -d'-' -f1)
OUTPUT_DIR="/tmp/pr-review-${PR_NUMBER}-${SESSION_ID}"
mkdir -p "$OUTPUT_DIR" && chmod 700 "$OUTPUT_DIR"  # restrict to current user

echo "Session output directory: $OUTPUT_DIR" >&2
```

**Why unique directory?**
- Prevents collisions when running multiple reviews concurrently
- All artifacts for one review grouped together
- Easy cleanup at end
- Clean isolation between sessions

If PR URL not found, ask user:
```
What's the PR URL? (e.g., https://github.com/org/repo/pull/123)
```

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
- `test_setup.can_run_safely`
- `security_sensitive`
- `impact_analysis`

**If analysis fails:**
- Log error
- Continue with limited information
- Note in final review: "⚠️ Change analysis failed"

## Step 3: Run Deep Code Review (3 parallel passes, one model each)

Run the deep code review inline — **spawn 3 independent bug-finders in parallel** with the Task tool. Each pass analyzes the same diff but may catch different issues; findings confirmed by multiple passes are high-confidence.

**Give each pass a different model.** Running the same model three times shares the same blind spots — three different models give genuinely independent perspectives, so a finding confirmed across models is far stronger signal, and the mix costs less than three deep-model passes. Assign models as:

| Pass | `model` value | Model ID | Role |
|------|---------------|----------|------|
| 1 | `opus` | `claude-opus-4-8` | Deepest reasoning — subtle logic, races, security data-flow |
| 2 | `sonnet` | `claude-sonnet-5` | Strong, different model family — diversifies findings |
| 3 | `haiku` | `claude-haiku-4-5` | Fast breadth pass — a cheap third independent perspective |

**Send ONE message with THREE Task tool calls.** For each:
- `subagent_type`: `general-purpose`
- `model`: the pass's model from the table above (`opus`, `sonnet`, `haiku` respectively). **Do not omit this** — an omitted `model` makes the pass inherit the session model, which collapses all three passes onto one model and defeats the diversity.
- `description`: `Bug hunter pass [1 opus / 2 sonnet / 3 haiku]`
- `prompt`: the Bug-Finder Prompt below, with the PR diff (from Step 2 / `gh pr diff <FULL_URL>`) inserted in place of `{{DIFF}}`.

**Don't wait for completion yet** — let these run while Step 4 proceeds; collect results in Step 6.

### Bug-Finder Prompt (use for all 3 passes)

```
You are a bug hunter. Find bugs that will crash production or create security vulnerabilities. Trace, don't scan.

## Critical Checks
- **NPE / null-deref:** for every dereference, trace the variable's lifecycle (declared? assigned? set null in cleanup/error paths? nulled by another thread?). Show the full trace for each risk.
- **Resource leaks:** every opened resource (connection, stream, file, cursor) — is it closed on all paths, including exceptions?
- **Security:** trace every external input (params, headers, API/DB reads) to dangerous sinks (SQL, HTML, shell, file paths, logs) without sanitization. Also flag hardcoded secrets, sensitive data in logs, missing auth checks.
- **Race conditions:** shared mutable state accessed without synchronization; check-then-act gaps.
- **Control flow:** missing returns after cleanup/error handling, early exits that skip cleanup, unreachable code.
- **Architectural:** inconsistent patterns (mixing two APIs for one purpose), wrappers/utilities removed without justification.

## Output
Return a JSON array of findings, each: {"severity":"critical|high|medium","path":"exact/path","line":N,"title":"5-10 words","body":"explanation with lifecycle/data-flow trace","suggestion":"concrete fix"}.
- `severity`: `critical` (crashes/security), `high` (fix soon), `medium` (fix later).
- `path`/`line` required when the issue maps to a diff location (`line` = NEW-file line, right side of diff); add `start_line` for multi-line. Omit both for general/architectural findings.
- Formatting for `title`, `body`, `suggestion`: wrap **every** code reference — identifiers, function/method/type names, file paths, config keys, literals, SQL — in `` `backticks` ``, and use fenced ```` ``` ```` blocks for multi-line snippets; never leave code as bare prose. Keep `body` to 1–2 terse sentences (or a couple of short bullets), not a paragraph.
- After the JSON, add a 1-2 sentence summary. Focus on crashes and vulnerabilities, not style.

## Code to Review
{{DIFF}}
```

**Merge (in Step 6):** group findings by `path` + `line`; prepend "[Found by N/3 models]" to any found by 2+ passes; take the highest severity. A finding surfaced by more than one model family is especially high-confidence — weight it accordingly in Step 7.

## Step 4: Run Phase 2 Skills (Parallel)

Now that we have the foundation (analysis + code review), run quality checks in parallel:

### 4.1 Launch Test Analysis (Sonnet subagent)

Run test-gap analysis in a **Task subagent pinned to a lower model** — assessing coverage and recommending tests is moderate reasoning over the diff and existing tests, well within Sonnet's range.
```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"   # mid-tier is sufficient for coverage/gap analysis; far cheaper than opus. Do not omit.
- description: "Test-gap analysis (sonnet)"
- prompt: |
    Invoke the Skill tool with skill "review:test-gaps" and args "<PR_URL> <OUTPUT_DIR>".
    Follow that skill exactly and write its output JSON to <OUTPUT_DIR> as the skill specifies
    ($OUTPUT_DIR/test-analysis-<PR_NUMBER>.json). Return a one-line summary of coverage and gaps.
```

### 4.2 Launch Security Scanner (Sonnet subagent)

Run security scanning in a **Task subagent pinned to a lower model** — it's mostly running tools (semgrep, linters, dependency checkers) and summarizing their output, which doesn't need the orchestrator's frontier model.
```
Use Task tool:
- subagent_type: "general-purpose"
- model: "sonnet"   # mid-tier: enough to interpret injection/crypto traces, far cheaper than opus. Do not omit.
- description: "Security scan (sonnet)"
- prompt: |
    Invoke the Skill tool with skill "review:security-scan" and args "<PR_URL> <OUTPUT_DIR>".
    Follow that skill exactly and write its output JSON to <OUTPUT_DIR> as the skill specifies
    ($OUTPUT_DIR/security-scan-<PR_NUMBER>.json). Return a one-line summary of the finding counts.
```

### 4.3 Launch Documentation Validator (Haiku subagent)

Run the docs drift/completeness check in a **Task subagent pinned to the cheapest model** — it's cross-file claim matching, not deep reasoning.
```
Use Task tool:
- subagent_type: "general-purpose"
- model: "haiku"    # cheapest tier is sufficient for doc claim/completeness matching. Do not omit.
- description: "Docs drift check (haiku)"
- prompt: |
    Invoke the Skill tool with skill "review:docs-drift" and args "<PR_URL> <OUTPUT_DIR>".
    Follow that skill exactly and write its output JSON to <OUTPUT_DIR> as the skill specifies
    ($OUTPUT_DIR/docs-drift-<PR_NUMBER>.json). Return a one-line summary.
```

**All three Phase 2 checks run in parallel as subagents on lower models** — test analysis (4.1) and security (4.2) on Sonnet, docs (4.3) on Haiku. Send the three Task calls in ONE message so they run concurrently, let them run while Step 5 proceeds, and collect in Step 6. They're independent (all consume the same analysis JSON) and none needs the orchestrator's frontier model.

**If any skill fails:**
- Log the error
- Continue with other skills
- Note in review: "⚠️ <skill> failed: <reason>"

## Step 5: Phase 3 - Test Execution and Code Generation (Conditional)

### 5.1 Test Execution (if safe)

**Check if tests can run safely from analysis JSON:**
```bash
CAN_RUN=$(jq -r '.test_setup.can_run_safely' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json")
```

**If tests can run safely:**
```
Use Skill tool:
- skill: "review:run-tests"
- args: "<PR_URL> <OUTPUT_DIR>"
```

**Wait for completion** and read results:
```bash
Read tool: $OUTPUT_DIR/test-results-<PR_NUMBER>.json
```

**If tests cannot run safely:**
- Skip test execution
- Note in review: "Tests cannot be run automatically (requires manual execution)"
- Provide test command from analysis JSON for manual execution

### 5.2 Code Generation (always run)

After test execution (or skip), generate code/docs:

```
Use Skill tool:
- skill: "review:codegen"
- args: "<PR_URL> <OUTPUT_DIR>"
```

**Wait for completion** and read results:
```bash
Read tool: $OUTPUT_DIR/code-generation-<PR_NUMBER>.json
```

**Code generation provides:**
- Test suggestions (code ready to add)
- Missing docstrings (ready to insert)
- CHANGELOG entry (ready to paste)
- API documentation (ready to add)
- Lint fixes (ready to apply)

**Note:** Generated code is for review only - not automatically committed.

## Step 6: Collect Results

**Wait for all skills to complete:**
- deep code review — 3 passes (Step 3)
- test-gaps (Step 4.1)
- security-scan (Step 4.2)
- docs-drift (Step 4.3)
- run-tests (Step 5.1) - if ran
- codegen (Step 5.2)

**Parse results from each skill:**

**Deep code review** — 3 passes (Step 3):
- Critical findings count
- High findings count
- Medium findings count

**test-gaps** (Step 4.1) - Read `$OUTPUT_DIR/test-analysis-<PR_NUMBER>.json`:
- Coverage percentage
- Untested areas count
- Test quality issues

**security-scan** (Step 4.2) - Read `$OUTPUT_DIR/security-scan-<PR_NUMBER>.json`:
- Critical security findings
- High security findings
- Dependency vulnerabilities

**docs-drift** (Step 4.3) - Read `$OUTPUT_DIR/docs-drift-<PR_NUMBER>.json`:
- Documentation status
- Missing docs count
- Required updates

**run-tests** (Step 5.1) - Read `$OUTPUT_DIR/test-results-<PR_NUMBER>.json` (if ran):
- Test execution status (passed/failed/timeout/skipped)
- Test counts (total, passed, failed)
- Execution time
- Failure details

**codegen** (Step 5.2) - Read `$OUTPUT_DIR/code-generation-<PR_NUMBER>.json`:
- Tests generated count
- Docstrings generated count
- CHANGELOG entries
- API docs sections
- Lint fixes

**change-analysis** (Step 2):
- Languages detected
- Frameworks found
- Impact areas
- Security sensitivity

## Step 7: Determine Merge Recommendation

Apply enhanced decision logic with Phase 2 findings:

```
IF (Critical code findings > 0) OR (Critical security findings > 0):
  RECOMMENDATION = "REQUEST CHANGES"
  RATIONALE = "Critical issues must be fixed before merge"

ELIF (High findings > 3) OR (security_sensitive AND high_security_findings > 0):
  RECOMMENDATION = "REQUEST CHANGES"
  RATIONALE = "Multiple high-severity issues require fixes"

ELIF (test_coverage < 60%) AND (new_features_added):
  RECOMMENDATION = "REQUEST CHANGES"
  RATIONALE = "Insufficient test coverage for new features (target: 80%)"

ELIF (High findings > 0) OR (missing_critical_docs):
  RECOMMENDATION = "COMMENT"
  RATIONALE = "Issues should be addressed (manual review required)"

ELIF (security_sensitive === true):
  RECOMMENDATION = "COMMENT"
  RATIONALE = "Security-sensitive changes require manual review"

ELSE:
  RECOMMENDATION = "COMMENT"
  RATIONALE = "Review completed - findings noted for consideration"
```

**Note:** Always default to COMMENT (not APPROVE) to maintain human-in-the-loop approval.

## Step 8: Build structured JSON for shared formatter

Build the review formatter input JSON with findings from all review stages. Map the 7 review sections to formatter sections:

### Construct the sections array

1. **Change Analysis** — body only (languages, frameworks, impact areas). No inline findings.
2. **Code Review Results (3 Passes)** — findings with `path`, `line`, `severity` from the 3-pass deep review (Step 3). These become inline comments.
3. **Test Analysis** — body only (coverage %, gaps, recommended tests). No inline findings.
4. **Security Analysis** — findings with `path`, `line`, `severity` where available (semgrep/bandit findings). These become inline comments. Non-line findings go in body.
5. **Documentation Check** — body only (README status, CHANGELOG, code comments). No inline findings.
6. **Test Execution Results** — body only (pass/fail counts, failures list). No inline findings.
7. **Code Generation** — body only (generated test suggestions, docstrings). No inline findings.

Set `review_metadata.model` to your own exact model ID (e.g. `claude-opus-4-8`), so the footer records which model orchestrated the review. Use the model ID from your environment context. Omit the field if you cannot determine it. Because the 3-pass code review ran on three different models, note the pass models (`claude-opus-4-8`, `claude-sonnet-5`, `claude-haiku-4-5`) in the "Code Review Results" section `body` so readers know the passes were model-diverse.

### Formatting rules for all prose (bodies, summary lines, rationale, actions)

Apply these to every `body`, `summary_line`, `rationale`, `required_actions`, and `optional_improvements` string:

- **Code references always in backticks.** Wrap identifiers, function/method/type names, file paths, config keys, literals, and SQL in `` `backticks` ``; use fenced ```` ``` ```` blocks for multi-line snippets. Never leave code as bare prose.
- **Bullets, not paragraphs.** Write each section `body` as a short markdown bullet list — one idea per bullet, laconic. Avoid runaway multi-sentence paragraphs; if a point needs two clauses, split it into two bullets.
- **Lead with the takeaway.** Each bullet states the conclusion first, supporting detail second.

### Build the JSON

```json
{
  "pr_url": "<FULL_PR_URL>",
  "recommendation": "<REQUEST_CHANGES|COMMENT>",
  "rationale": "<Brief summary from Step 7>",
  "required_actions": ["<action1>", "<action2>"],
  "optional_improvements": ["<suggestion1>"],
  "sections": [
    {
      "title": "Change Analysis",
      "summary_line": "<X files, Y+ Z- lines, primary language>",
      "body": "<Change analysis — bullets>"
    },
    {
      "title": "Code Review Results (3 Passes)",
      "summary_line": "X Critical, Y High, Z Medium",
      "body": "<Consensus analysis — bullets>",
      "findings": [<code review finding objects with path, line, severity>]
    },
    {
      "title": "Test Analysis",
      "summary_line": "<coverage>% coverage (<tested>/<changed> lines)",
      "body": "<Test analysis — bullets: gaps + recommended tests>"
    },
    {
      "title": "Security Analysis",
      "summary_line": "X Critical, Y High, Z Medium, W Low",
      "body": "<Security summary — bullets>",
      "findings": [<security finding objects with path, line where available>]
    },
    {
      "title": "Documentation Check",
      "summary_line": "<Complete|Needs Updates|Incomplete>",
      "body": "<Documentation check — bullets>"
    },
    {
      "title": "Test Execution Results",
      "summary_line": "<X passed, Y failed, Z skipped>",
      "body": "<Test execution results — bullets>"
    },
    {
      "title": "Code Generation",
      "summary_line": "<X tests, Y docstrings, Z docs generated>",
      "body": "<Code generation suggestions — bullets>\n\n**All generated code requires human review before committing.**"
    }
  ],
  "review_metadata": {
    "tool_name": "review",
    "review_title": "Review",
    "tool_version": "<read from .claude-plugin/plugin.json — do not hardcode>",
    "model": "<your exact model ID, e.g. claude-opus-4-8>",
    "stages": ["Change Analysis", "Code Review", "Test Analysis", "Security", "Documentation", "Test Execution", "Code Generation"]
  }
}
```

**Note:** Omit sections that were skipped or failed. The formatter automatically omits empty sections.

**Note:** Set `review_metadata.tool_version` to the `version` field read from `.claude-plugin/plugin.json` so the posted review always reflects the installed version. Do not hardcode it.

## Step 9: Post review via shared formatter

Write the JSON to the session directory (`$OUTPUT_DIR/review-payload.json`) and pipe it to the formatter:

```bash
cat "$OUTPUT_DIR/review-payload.json" | python3 scripts/review_formatter.py --post
```

If `--post` fails, fall back to `--dry-run` and show the formatted body to the user:

```bash
cat "$OUTPUT_DIR/review-payload.json" | python3 scripts/review_formatter.py --dry-run
```

The formatter will:
- Post inline comments on specific lines where code review and security findings have `path` + `line`
- Post a collapsible summary with up to 7 sections as the top-level review body
- Use the correct GitHub review event (REQUEST_CHANGES or COMMENT)

**Note:** Always default to COMMENT (not APPROVE) to maintain human-in-the-loop approval.

## Step 10: Provide User Summary

Display concise summary:

```
Comprehensive Review Complete

Summary:
- Languages: <primary> (<percentage>%)
- Code Review: <X Critical, Y High, Z Medium>
- Test Coverage: <percentage>% (target: 80%)
- Security: <X Critical, Y High findings>
- Documentation: <Complete | Needs Updates>
- Tests Executed: <Passed | Failed | Skipped>
- Code Generated: <count> tests, <count> docstrings, <count> docs
- Recommendation: <REQUEST CHANGES | COMMENT>

View full review: <PR_URL>
```

## Error Handling

### If analyze fails:
- Continue with the deep code review only
- Omit Change Analysis section from JSON
- Note in rationale: "Change analysis unavailable"

### If the deep code review fails:
- Omit Code Review section from JSON
- Base recommendation on other findings only
- Recommend manual code review in rationale

### If both fail:
- Error message: "Could not complete review - please check PR access and try again"
- Do not post incomplete review

### If PR posting fails:
- Use `--dry-run` to show formatted review to user
- Suggest manual copy/paste
- Save review JSON to `$OUTPUT_DIR/review-<PR_NUMBER>.json`

## Notes

- This skill is the entry point for comprehensive reviews
- It runs a model-diverse 3-pass deep code review (opus + sonnet + haiku) and coordinates 6 skills: analyze, test-gaps, security-scan (sonnet subagent), docs-drift (haiku subagent), run-tests, codegen
- Designed to be extended as new skills are added
- Always maintains human-in-the-loop (never auto-approves/merges)
- Generated code requires human review before committing
- Cost: ~$3-7 per PR (model-diverse 3-pass deep review — one opus + one sonnet + one haiku — plus 6 analysis/execution skills; cheaper and higher-signal than three opus passes)
