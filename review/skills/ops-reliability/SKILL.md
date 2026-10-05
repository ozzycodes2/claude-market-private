---
name: ops-reliability
description: Reviews PR diffs for reliability, operability, performance, and leftover concurrency hazards beyond race hunting. Use when analyze risk_class includes ops or concurrency, or when a PR adds dependencies, queues, retries, or hot-path work.
allowed-tools: Bash Read Grep Glob
---

# Ops & Reliability Review

Quality Review pass covering taxonomy categories **8 Reliability & operability**, **10 Performance & scalability**, plus concurrency leftovers beyond the bug-finder's race focus (DLQ/poison, async cancellation leftovers, ordering). Emits Conventional Comment findings in the bug-finder schema.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Defaults to private `mktemp -d`
- **Analysis JSON** (optional): `$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json`

## Outputs

Writes `$OUTPUT_DIR/ops-reliability-<PR_NUMBER>.json`:

```json
{
  "pr_number": 123,
  "pass": "ops-reliability",
  "findings": [
    {
      "severity": "critical|high|medium",
      "label": "issue|suggestion|nitpick|question|thought|praise",
      "decoration": "blocking|non-blocking|if-minor",
      "path": "exact/path",
      "line": 42,
      "title": "5-10 words",
      "body": "explanation",
      "suggestion": "concrete fix"
    }
  ]
}
```

## Step 0: Parse arguments

```bash
PR_URL="$1"
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"
mkdir -p "$OUTPUT_DIR"
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
```

## Step 1: Load context (progressive disclosure)

1. Read `references/anti-patterns.md`.
2. Read this skill's `references/checklist.md`.
3. Optionally skim `shared/severity-rubric.md`.
4. If present, read analysis JSON for ops/hot-path hints.

## Step 2: Fetch PR diff

```bash
gh pr diff "$PR_URL" > "$OUTPUT_DIR/pr.diff"
gh pr view "$PR_URL" --json title,body,files,additions,deletions
```

Focus on clients/HTTP calls, queues/consumers, retries/timeouts, caches, pagination, resource pools, metrics/logging on new paths.

## Step 3: Review

Walk checklist: failure modes → timeouts/retries/isolation → observability → performance → concurrency leftovers. Apply Clean Code as **blocking** when craft issues obscure failure modes on shared/hot paths.

Do **not** re-litigate basic race/NPE hunting (bug-finder owns that); focus on operational consequences and leftover concurrency classes listed in the checklist.

## Step 4: Emit JSON

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg pass "ops-reliability" \
  --argjson findings "$FINDINGS_JSON" \
  '{pr_number: $pr_number, pass: $pass, findings: $findings}' \
  > "$OUTPUT_DIR/ops-reliability-${PR_NUMBER}.json"
```

## Notes

- Standalone: `/review:ops-reliability <PR_URL> [OUTPUT_DIR]`
- Orchestrator runs when `ops` or `concurrency` ∈ `risk_class`
