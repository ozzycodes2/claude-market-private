---
name: docs-drift
description: >
  Detect documentation drift in a repo's docs/ folder — ADRs, glossaries, API
  specs (OpenAPI), rendered artifacts, READMEs, code comments, runbooks, and
  caller-migration notes — that has fallen out of sync with the code a PR
  changes, and flag documentation-completeness gaps (missing CHANGELOG/README/
  docstring updates). Use when reviewing a PR to verify docs still describe the
  CURRENT model: stale comments describing a removed mechanism, docs asserting a
  superseded design, a rendered file lagging its source, ADR index rows that
  don't reflect an amendment or supersede, env/config docs that name the wrong
  app or variable, missing runbooks for ops-facing changes, or missing caller
  migration notes for breaking APIs. Use even when the PR doesn't obviously
  touch docs — code changes silently invalidate docs elsewhere in the tree.
allowed-tools: Bash Read Grep Glob
metadata:
  author: machinify
  facet-of: review
---

# Documentation Drift & Completeness Check

Two facets, one skill:

- **Drift** — docs that now *contradict the code* (or each other) after the
  PR's changes. The hard part: the drift lives in a file the PR did
  not touch, so a diff-only reviewer never sees it.
- **Completeness** — expected doc updates the PR *should have made but didn't*
  (CHANGELOG entry, README/API doc for a new surface, docstrings on new public
  items, light DX: ADR/runbook/caller migration).

The generative insight (from real multi-round PR reviews): most doc findings
surface one commit at a time because each is a *cross-file* claim — a sentence
in `docs/` asserting a code fact that a later commit quietly falsified. Catch
them by extracting every doc claim that references a code fact, then verifying
each claim against the post-change code in ONE pass.

## Inputs

- **PR URL** — full GitHub/Enterprise URL.
- **OUTPUT_DIR** (optional) — defaults to a private `mktemp -d`.
- **Analysis JSON** — `<OUTPUT_DIR>/pr-analysis-<PR_NUMBER>.json` from the
  `analyze` skill, if present (gives changed files + languages).

## Output

Write findings to `<OUTPUT_DIR>/docs-drift-<PR_NUMBER>.json`. Use the template
in `assets/docs-drift.output.json` verbatim as the shape. Findings that map to
a specific doc line carry `path` + `line` so the orchestrator posts them
inline; cross-file/architectural findings omit both and go in the section body.

Build the JSON with `jq -n` and `--arg`/`--argjson` so doc text is escaped —
never heredoc untrusted strings.

## Workflow

Progress:
- [ ] Step 1 — Inventory the docs surface (`scripts/docs_inventory.py`)
- [ ] Step 2 — Extract code-referencing claims from docs
- [ ] Step 3 — Verify each claim against the changed code (plan → validate)
- [ ] Step 4 — ADR-specific cross-checks (index ↔ files ↔ status)
- [ ] Step 5 — Rendered-artifact staleness (source ↔ generated)
- [ ] Step 6 — Completeness gaps (+ light DX fold)
- [ ] Step 7 — Score + emit JSON
- [ ] Step 8 — Validate every finding, drop the confirmations, then write it out

### Step 0: Parse arguments

```bash
PR_URL="$1"
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
```

### Step 1: Inventory the docs surface

```bash
python3 scripts/docs_inventory.py --repo-root "$REPO_ROOT" > "$OUTPUT_DIR/docs-inventory.json"
gh pr diff "$PR_URL" --patch > "$OUTPUT_DIR/pr.diff"
gh pr diff "$PR_URL" --name-only > "$OUTPUT_DIR/pr.files"
```

### Step 2: Extract claims

Read `references/drift-patterns.md` — authoritative catalog of drift
classes. Work through it; do not improvise categories.

A **claim** is any doc sentence, table row, code comment, or config comment
asserting a *checkable code fact*. Collect claims from every doc the inventory
found — not only docs in the PR diff.

### Step 3: Verify each claim against the changed code

For every claim, locate the code fact in the post-change tree and decide
`intact | drifted | uncertain`. Prefer grepping the repo at HEAD over memory.
A claim is **drifted** when the asserted fact is absent, renamed, or replaced.
Record doc line AND contradicting code location in the finding body.

### Step 4: ADR cross-checks

If `docs/adrs/` exists, verify ADR bookkeeping the inventory extracted (status
reflected in index, supersede links bidirectional, model changes retire old docs).

### Step 5: Rendered-artifact staleness

For each source→rendered pair: if source changed but rendered did not (or still
contains old strings), flag it. Prefer "regenerate" when CI/hooks own the artifact.

### Step 6: Completeness gaps

- New public surface (endpoint, exported type, CLI flag, env var) with no
  matching README/API-doc/`dot-env` entry.
- Behavior change with no CHANGELOG entry (only if the repo keeps one).
- New public items missing docstrings (only to the repo's existing bar).

#### DX docs fold (light touch)

When the PR changes behavior that operators or callers must know about, also check:

- **ADRs** — behavior/architecture shift without ADR add/amend/supersede when the repo keeps ADRs
- **Runbooks / ops notes** — deploy, rollback, feature-flag, or on-call steps when ops behavior changes
- **Caller migration** — breaking internal/public APIs without examples, codemods, or deprecation notes for callers

Keep this light: only flag when the gap would mislead a teammate or on-call. Do not invent a docs policy the repo does not hold.

### Step 7: Score & emit

Severity: **high** = a doc actively misleads; **medium** = stale but not
dangerous; **low** = cosmetic/index bookkeeping. Emit JSON per the asset template.

### Step 8: Validation loop

For each finding: (1) quotes the doc line, (2) names contradicting code or missing
artifact, (3) severity matches rubric. Drop unverifiable claims.

**Then drop every finding whose remedy is a confirmation.** `fix` works this
list to completion, so a finding with nothing to edit becomes a deferral that
costs a routing decision and a report line and changes no file. Drop it when:

- the remedy's verb is *confirm*, *verify*, *check*, *ensure*, *consider*,
  *be aware*, or *no action needed*;
- it restates that the doc and the code agree;
- it reports an absence the repo has no policy about (no CHANGELOG in a repo
  that keeps none, no ADR for a change the ADR index does not cover);
- it is cosmetic drift in a generated artifact that the next regeneration fixes.

Keep the finding when a reader of the current doc would act wrongly.

Then write `docs-drift-<PR_NUMBER>.json`.

## mac-ui repos (Machinify Web Components)

When the repo is or consumes `@vlognow/mac-ui`, resolve docs live. Read
`references/mac-ui-docs.md` for the fetch recipe.

## Gotchas

- Drift usually lives OUTSIDE the diff. Inventory the whole `docs/` tree.
- Rendered artifacts: fix is regeneration, not hand-edit.
- Code comments count as docs.
- Don't flag drift from memory — mark `uncertain` when greps are inconclusive.

## Files

- `references/drift-patterns.md` — drift-class catalog (read in Step 2).
- `references/mac-ui-docs.md` — how to fetch mac-ui's live docs.
- `assets/docs-drift.output.json` — output JSON template.
- `scripts/docs_inventory.py` — docs/ADR/rendered inventory (`--help`).
- `evals/evals.json` — trigger + output evals.
