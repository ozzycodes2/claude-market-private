---
name: domain-architecture
description: Reviews PR diffs for domain model integrity, architecture dependency rules, and team/org boundary risks. Use when analyze risk_class includes domain, or when a PR crosses bounded contexts, ownership, or layering boundaries.
allowed-tools: Bash Read Grep Glob
---

# Domain & Architecture Review

Quality Review pass covering taxonomy categories **1 Domain**, **2 Architecture**, and **15 Team/org boundaries**. Emits Conventional Comment findings in the same schema as the bug-finder.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Defaults to private `mktemp -d`
- **Analysis JSON** (optional): `$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json` from `analyze`

## Outputs

Writes `$OUTPUT_DIR/domain-architecture-<PR_NUMBER>.json`:

```json
{
  "pr_number": 123,
  "pass": "domain-architecture",
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

`path`/`line` required when the issue maps to a diff location (`line` = NEW-file line). Omit both for architectural findings. Omit `label`/`decoration` to accept severity defaults (see `../../references/severity-rubric.md`).

## Step 0: Parse arguments

```bash
PR_URL="$1"
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"
mkdir -p "$OUTPUT_DIR"
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
```

## Step 1: Load context (progressive disclosure)

1. Read **only** `../../references/anti-patterns/domain-architecture.md` — do **not** read other anti-pattern files.
2. Read this skill's `references/checklist.md` for dimensions.
3. Optionally skim `../../references/severity-rubric.md` for Clean Code blocking rules.
4. If present, read `$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json` for impact hints.

## Step 2: Fetch PR diff

```bash
gh pr diff "$PR_URL" > "$OUTPUT_DIR/pr.diff"
gh pr view "$PR_URL" --json title,body,files,additions,deletions
```

## Step 3: Review

Walk checklist dimensions in order: domain → architecture → team boundaries. Apply Clean Code as **blocking** when craft issues hit correctness, invariants, or maintainability on shared/hot paths (not deferred to nits).

Prioritize:

1. Bounded context / ubiquitous language conflicts on public surfaces
2. Aggregate invariants and layering violations
3. Dependency direction / circular coupling / undeclared blast radius
4. Ownership and cross-team contract breaks

## Step 4: Emit JSON

Build with `jq -n` and `--arg`/`--argjson` so diff text is escaped. Write findings array; empty array is valid.

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg pass "domain-architecture" \
  --argjson findings "$FINDINGS_JSON" \
  '{pr_number: $pr_number, pass: $pass, findings: $findings}' \
  > "$OUTPUT_DIR/domain-architecture-${PR_NUMBER}.json"
```

## Notes

- Standalone: `/review:domain-architecture <PR_URL> [OUTPUT_DIR]`
- Orchestrator gates this pass when `domain` ∈ `risk_class` (see `../../references/risk-class-routing.md`)
- Do not rubber-stamp large boundary-crossing PRs; prefer `question` when ownership is unclear
