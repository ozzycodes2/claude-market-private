---
name: codegen
description: Generates simple tests, docstrings, and documentation updates for PR changes. Use when reviewing a PR and you want draft tests, docstrings, or CHANGELOG entries to fill the gaps it surfaced (human review required before committing).
allowed-tools: Bash Read Write
metadata:
  author: machinify
  facet-of: review
---

# Code Generator

Generates simple, low-risk code and documentation for PR changes — "easy wins":
tests for simple functions, missing docstrings, CHANGELOG entries, API docs.
Everything it emits is a *draft for human review*, never auto-committed.

## Inputs

- **PR URL** — full GitHub/Enterprise URL.
- **OUTPUT_DIR** (optional) — defaults to a private `mktemp -d`.
- **Analysis JSON** — `analyze` at `$OUTPUT_DIR/pr-analysis-<number>.json`
  (languages, frameworks, `test_setup.framework`, `uses_mac_ui`).
- **Docs Drift JSON** — `docs-drift` at `$OUTPUT_DIR/docs-drift-<number>.json`
  (completeness findings — `facet: "completeness"`, `drift_class: "missing-doc"`
  — name the missing docstring / CHANGELOG / API-doc surfaces).

## Output

`$OUTPUT_DIR/code-generation-<PR_NUMBER>.json` (structure in Step 7) plus a
human-readable `code-generation-<PR_NUMBER>-summary.md` (template in
`references/output-examples.md`).

## Step 0: Parse arguments

```bash
PR_URL="$1"
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
```

## Prerequisites

```bash
cat "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
cat "$OUTPUT_DIR/docs-drift-${PR_NUMBER}.json"
```

## Step 1: Determine what to generate

**Generate only** LOW-complexity, LOW-risk, HIGH-confidence items: simple
getters/setters/validators/formatters, missing docstrings, CHANGELOG entries,
API docs for new endpoints, trivial lint fixes.

**Never generate:** business logic, DB migrations, endpoint implementations,
auth/authz logic, or anything needing domain knowledge.

Parse the inputs: identify simple, untested functions directly from the PR diff
(cross-checking the changed files for an existing test); completeness gaps from
docs-drift; language/framework/`uses_mac_ui` from analysis.

## Step 2: Generate tests (conservative)

Candidates: pure functions, simple validators, data transformers, property
accessors — under 20 lines, no external deps, no existing test. Use the
skeletons in `references/generation-templates.md` (Python/JS/Go/Java/**Rust**).

Rules: max 3 tests per function (happy + ≤2 edge/error cases); skip complex,
side-effecting, or already-tested functions. For Rust, prefer filling an exact
untested branch/arm visible in the diff (e.g. an env-parse `unset|blank|invalid`
arm) over a bare happy path, and place tests in the file's `#[cfg(test)] mod
tests` block.

## Step 3: Generate docstrings

For each completeness `missing-doc` finding on a public item, generate a
docstring in the language's convention (templates in
`references/generation-templates.md`). Document params, returns, and errors;
omit internals. Match the file's existing docstring density; 2-10 lines.

## Step 4: Generate CHANGELOG entries

Only if the repo keeps a CHANGELOG. Group PR commits into Added/Changed/Fixed/
Deprecated/Removed/Security (Keep a Changelog style):

```bash
gh pr view "$PR_URL" --json commits --jq '.commits[].messageHeadline'
```

Determine the version bump per the table in `references/output-examples.md`.

## Step 5: Generate API documentation

For each new/changed endpoint the completeness findings flagged, emit an
OpenAPI-style markdown section (template in `references/generation-templates.md`):
method+path, request (headers/body), response (success/error), error codes.
Omit internals. For an OpenAPI-first repo, prefer proposing the spec edit and
let the render regenerate, rather than hand-writing prose (see `docs-drift`).

## Step 6: Generate lint fixes

Only trivial issues: unused variable → `_`-prefix, trailing commas, whitespace,
import ordering. Never fix logic/type errors. Emit `{file, line, issue, fix,
diff}`.

## Step 7: Output JSON

Build with `jq -n`, every generated snippet passed via `--arg` (never heredoc
model/PR-derived text). Emit `generated.{tests,docstrings,changelog_entries,
api_docs,lint_fixes}` (each entry carries `file`, `reason`, `confidence`),
plus `stats` counts and a one-line `summary`:

```bash
jq -n --argjson pr_number "$PR_NUMBER" --arg ts "$(date -Iseconds)" \
  --arg test_code "$TEST_CODE" --arg docstring "$DOCSTRING" \
  '{ pr_number:$pr_number, generation_timestamp:$ts, status:"completed",
     generated:{ tests:[{file:"…",function:"…",code:$test_code,reason:"…",confidence:"high"}],
                 docstrings:[{file:"…",line:0,docstring:$docstring,reason:"…",confidence:"high"}],
                 changelog_entries:[], api_docs:[], lint_fixes:[] },
     stats:{tests_generated:0,docstrings_generated:0,changelog_entries:0,api_docs_sections:0,lint_fixes:0},
     review_required:true,
     summary:"…" }' > "$OUTPUT_DIR/code-generation-${PR_NUMBER}.json"
```

Then write the human-readable summary per `references/output-examples.md`.

## Step 8: Safety & confidence

Validate each snippet (syntax, imports, naming convention) before emitting.
Confidence: **HIGH** (validators/getters/formatters), **MEDIUM** (CHANGELOG,
API docs). Emit HIGH+MEDIUM only — drop LOW. Always set `review_required:true`
with concrete review notes (verify assertions match behavior; check CHANGELOG
version against the release plan; validate API examples).

## Step 9: Summary

Report counts by artifact and confidence, and remind that human review is
required before committing. Point the reviewer at the JSON + summary files.

## Limitations

Does NOT generate business logic, DB migrations, endpoint implementations, or
architectural decisions; does NOT modify existing tests or auto-commit. DOES
draft simple tests, docstrings, CHANGELOG entries, API docs, and trivial lint
fixes — all for review.

## Error handling

If an item fails, continue with the rest and record it under `skipped` with a
reason and a manual-write recommendation (example in
`references/output-examples.md`).

## Integration & notes

Called by `review` in Phase 3. Conservative by design: only
easy, well-established patterns; skip anything ambiguous. Cost ~$0.50-1.50/PR.

## Files

- `references/generation-templates.md` — per-language test/docstring/API skeletons.
- `references/output-examples.md` — human-summary template, version-bump table,
  skipped-item record.
