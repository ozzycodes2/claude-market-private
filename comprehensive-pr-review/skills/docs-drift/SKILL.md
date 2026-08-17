---
name: docs-drift
description: >
  Detect documentation drift in a repo's docs/ folder — ADRs, glossaries, API
  specs (OpenAPI), rendered artifacts, READMEs, and code comments — that has
  fallen out of sync with the code a PR changes, and flag documentation-
  completeness gaps (missing CHANGELOG/README/docstring updates). Use when
  reviewing a PR to verify docs still describe the CURRENT model: stale comments
  describing a removed mechanism, docs asserting a superseded design, a rendered
  file lagging its source, ADR index rows that don't reflect an amendment or
  supersede, and env/config docs that name the wrong app or variable. Use even
  when the PR doesn't obviously touch docs — code changes silently invalidate
  docs elsewhere in the tree.
allowed-tools: Bash Read Grep Glob
metadata:
  author: machinify
  facet-of: comprehensive-pr-review
---

# Documentation Drift & Completeness Check

Two facets, one skill:

- **Drift** — docs that now *contradict the code* (or each other) after the
  PR's changes. This is the hard part: the drift lives in a file the PR did
  not touch, so a diff-only reviewer never sees it.
- **Completeness** — expected doc updates the PR *should have made but didn't*
  (CHANGELOG entry, README/API doc for a new surface, docstrings on new public
  items).

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
- [ ] Step 6 — Completeness gaps
- [ ] Step 7 — Score + emit JSON
- [ ] Step 8 — Validate every finding before writing it out

### Step 0: Parse arguments

```bash
PR_URL="$1"
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
```

### Step 1: Inventory the docs surface

Run the inventory script — it emits structured JSON (docs tree, ADR files vs
index rows, source→rendered pairs, CHANGELOG/README presence) to stdout and
diagnostics to stderr:

```bash
python3 scripts/docs_inventory.py --repo-root "$REPO_ROOT" > "$OUTPUT_DIR/docs-inventory.json"
```

Also capture the PR diff once, with context, for claim verification:

```bash
gh pr diff "$PR_URL" --patch > "$OUTPUT_DIR/pr.diff"
gh pr diff "$PR_URL" --name-only > "$OUTPUT_DIR/pr.files"
```

### Step 2: Extract claims

Read `references/drift-patterns.md` — it is the authoritative catalog of drift
classes with a detection heuristic and a real example for each. Work through
it; do not improvise categories.

A **claim** is any doc sentence, table row, code comment, or config comment
that asserts a *checkable code fact*: a module path, type/function name, an
endpoint, an env var name, a file that is generated from another, a PHI/data
model statement, an ADR status, or "X is wired to Y". Collect claims from every
doc the inventory found — not only docs in the PR diff.

### Step 3: Verify each claim against the changed code (plan-validate-execute)

For every claim, locate the code fact it references in the post-change tree and
decide `intact | drifted | uncertain`. Prefer grepping the repo at HEAD over
reasoning from memory:

```bash
# Does the module path / symbol / endpoint the doc names still exist?
grep -rn "ZoomCcChannel" "$REPO_ROOT/crates" || echo "SYMBOL GONE — doc may be stale"
```

A claim is **drifted** when the code fact it asserts is absent, renamed, or
replaced in the post-change tree. Record the doc line AND the contradicting
code location (or "removed by <sha>") in the finding body — a finding without
both halves is not verified (see Step 8).

### Step 4: ADR cross-checks

If `docs/adrs/` exists, verify the ADR bookkeeping the inventory extracted:

- Every ADR file's `Status` (`Accepted`, `Superseded by NNNN`, `Accepted
  (Amended by NNNN)`) is reflected in the index/README table, and vice versa.
- A superseding ADR names `Supersedes NNNN` and the superseded one points back.
- A new ADR that changes a model retires the docs describing the old model
  (this is the cross-link into Step 3).

### Step 5: Rendered-artifact staleness

For each source→rendered pair the inventory found (e.g. `openapi.yaml` →
`api/index.html`, a `.md` → its site render), if the source is in the diff but
the rendered artifact is not — or the rendered artifact still contains a string
the source just changed — flag it. Note whether a hook/CI step regenerates it
(if so, the fix is "regenerate", not hand-edit).

### Step 6: Completeness gaps

- New public surface (endpoint, exported type, CLI flag, env var) with no
  matching README/API-doc/`dot-env` entry.
- Behavior change with no CHANGELOG entry (only if the repo keeps one).
- New public items missing docstrings (only to the repo's existing bar — do
  not invent a docstring policy the repo doesn't hold).

### Step 7: Score & emit

Severity: **high** = a doc actively misleads (wrong credential, superseded PHI
model, an instruction that cannot work as written); **medium** = stale but not
dangerous; **low** = cosmetic/index bookkeeping. Emit the JSON per the asset
template.

### Step 8: Validation loop (do this before writing the file)

For each finding, self-check: (1) it quotes the doc line, (2) it names the
contradicting code location or the missing artifact, (3) severity matches the
rubric. Drop any finding that fails — an unverifiable drift claim is noise.
Then write `docs-drift-<PR_NUMBER>.json`.

## mac-ui repos (Machinify Web Components)

When the repo is or consumes `@vlognow/mac-ui`, its docs are authoritative and
**change frequently**, so resolve them live rather than trusting this skill's
memory. Read `references/mac-ui-docs.md` for the fetch recipe and the specific
files (ADRs under `docs/adrs/`, the `ai-*` spec set, per-component `mac-*.md`).

## Gotchas

- Drift usually lives OUTSIDE the diff. Inventory the whole `docs/` tree, not
  just changed files, or you reproduce the diff-only blind spot.
- A rendered artifact (`index.html`, a built site) is not "docs you edit" — its
  drift fix is regeneration. Say so instead of proposing a hand-edit.
- Code comments count as docs. A comment describing a mechanism a commit
  removed is drift even though it sits in a `.rs`/`.ts` file, not `docs/`.
- Don't flag a doc as drifted from memory. If a symbol/endpoint grep is
  inconclusive, mark the claim `uncertain` and put it in the body, not inline.

## Files

- `references/drift-patterns.md` — drift-class catalog (read in Step 2).
- `references/mac-ui-docs.md` — how to fetch mac-ui's live docs.
- `assets/docs-drift.output.json` — output JSON template.
- `scripts/docs_inventory.py` — docs/ADR/rendered inventory (`--help`).
- `evals/evals.json` — trigger + output evals.
