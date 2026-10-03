---
name: data-contracts
description: Reviews PR diffs for data consistency, schema/migration safety, and API/event contract compatibility. Use when analyze risk_class includes data or api, or when a PR changes schemas, migrations, public APIs, or event payloads.
allowed-tools: Bash Read Grep Glob
---

# Data & Contracts Review

Quality Review pass covering taxonomy categories **7 Data & consistency** and **11 API / contract design**. Emits Conventional Comment findings in the bug-finder schema.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Defaults to private `mktemp -d`
- **Analysis JSON** (optional): `$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json`

## Outputs

Writes `$OUTPUT_DIR/data-contracts-<PR_NUMBER>.json`:

```json
{
  "pr_number": 123,
  "pass": "data-contracts",
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

1. Read **only** `references/anti-patterns/data-contracts.md`.
2. Read `references/checklist.md` in this skill.
3. Optionally skim `references/severity-rubric.md`.
4. If present, read analysis JSON for schema/API impact hints.

## Step 2: Fetch PR diff

```bash
gh pr diff "$PR_URL" > "$OUTPUT_DIR/pr.diff"
gh pr view "$PR_URL" --json title,body,files,additions,deletions
```

Focus on migrations, schema files, serializers, OpenAPI/Protobuf/Avro, handlers with writes, public route/event definitions.

## Step 3: Review

Walk checklist: data/consistency first, then API/contracts. Apply Clean Code as **blocking** when craft issues hit correctness, invariants, or maintainability on shared contract/hot write paths.

Prioritize:

1. Migration expand/contract and integrity constraints
2. Idempotency under at-least-once / dual-write hazards
3. Backward compatibility and versioning of APIs/events
4. PII minimization and delete/retention paths when in scope

## Step 4: Emit JSON

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg pass "data-contracts" \
  --argjson findings "$FINDINGS_JSON" \
  '{pr_number: $pr_number, pass: $pass, findings: $findings}' \
  > "$OUTPUT_DIR/data-contracts-${PR_NUMBER}.json"
```

## Notes

- Standalone: `/review:data-contracts <PR_URL> [OUTPUT_DIR]`
- Orchestrator runs when `data` or `api` ∈ `risk_class`

Paths like `references/...` are relative to the `review` plugin root.
