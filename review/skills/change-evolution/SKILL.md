---
name: change-evolution
description: Reviews PR diffs for CD readiness, reversibility, and design-quality risks such as YAGNI, deep modules, and complexity budget. Use when a PR is large, mixes refactor with behavior, or introduces flags/migrations/stranglers.
allowed-tools: Bash Read Grep Glob
---

# Change & Evolution Review

Quality Review pass covering taxonomy categories **5 Change & evolution (CD)** and **4 Design quality**. Emits Conventional Comment findings in the bug-finder schema.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Defaults to private `mktemp -d`
- **Analysis JSON** (optional): `$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json`

## Outputs

Writes `$OUTPUT_DIR/change-evolution-<PR_NUMBER>.json`:

```json
{
  "pr_number": 123,
  "pass": "change-evolution",
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

1. Read **only** `references/anti-patterns/change-evolution.md`.
2. Read `references/checklist.md` in this skill.
3. Optionally skim `references/severity-rubric.md`.
4. If present, read analysis JSON for impact and `risk_class`.

## Step 2: Fetch PR diff

```bash
gh pr diff "$PR_URL" > "$OUTPUT_DIR/pr.diff"
gh pr view "$PR_URL" --json title,body,files,additions,deletions,commits
```

## Step 3: Review

Walk checklist: CD readiness / reversibility first, then design quality (YAGNI, deep modules, complexity). Apply Clean Code as **blocking** when craft issues hit correctness, invariants, or maintainability on shared/hot paths.

Prioritize:

1. Releasability of each merge; feature-flag defaults; rollback
2. Expand/contract and deploy ordering
3. Refactor mixed with behavior; PR size / one concern
4. Speculative generality and complexity budget on shared modules

## Step 4: Emit JSON

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg pass "change-evolution" \
  --argjson findings "$FINDINGS_JSON" \
  '{pr_number: $pr_number, pass: $pass, findings: $findings}' \
  > "$OUTPUT_DIR/change-evolution-${PR_NUMBER}.json"
```

## Notes

- Standalone: `/review:change-evolution <PR_URL> [OUTPUT_DIR]`
- Orchestrator runs on large/mixed/CD/design signals (see `risk-class-routing.md`)

Paths like `references/...` are relative to the `review` plugin root.
