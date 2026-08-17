# Drift-class catalog

Each class below is a *cross-file* failure: a doc claim that a code change
falsified. For each, use the detection heuristic to find candidates, then
verify against the post-change tree (SKILL.md Step 3). Examples are drawn from
real multi-round reviews where these surfaced one commit at a time.

## 1. Stale comment describing a removed mechanism

A code comment or doc explains *how* something works, but the commit that
changed the code left the prose describing the old mechanism.

- **Heuristic:** for each comment/doc sentence that describes a behavior
  ("collapses to `\"\"`", "falls back to X", "reads header Y"), grep the
  current code for the mechanism it names. Gone/changed → drift.
- **Example:** a comment "an absent header collapses to `\"\"`" after the
  extractor was changed to pass `None` through.

## 2. Doc asserts a superseded model

An ADR or design doc changed the model (PHI location, auth default, data
boundary), but other docs still state the old model.

- **Heuristic:** when an ADR is `Superseded`/`Amended` in this PR (or recently),
  grep every doc + README + comment for the old model's phrasing and confirm
  each was updated.
- **Example:** README/OpenAPI still say "transcript comes from S3" after an ADR
  moved the transcript to a read-delegate model.

## 3. Rendered artifact lags its source

A generated file (`index.html` from `openapi.yaml`, a built docs site) still
carries text the source just changed.

- **Heuristic:** from the inventory's source→rendered pairs, if source is in the
  diff and the rendered file still contains the pre-change string, flag. Check
  for a regen hook/CI step; fix = "regenerate", not hand-edit.
- **Example:** `openapi.yaml` fixed a description; committed `api/index.html`
  Redoc render still shows the old one and the staleness gate can't see it.

## 4. ADR index ↔ file disagreement

The ADR index/README table and the ADR files disagree on status, amendment, or
supersede links.

- **Heuristic:** diff the inventory's `adr_files` status against `adr_index`
  rows. New rows carrying an amendment while the amended row stays unqualified =
  drift; a `Supersedes`/`Superseded by` without its reciprocal = drift.

## 5. Env/config doc names the wrong thing

`dot-env`/README documents a variable or credential that names a different
app/component than the code actually reads, so following it verbatim breaks.

- **Heuristic:** for each documented env var, grep the code for the reader; if
  the doc's stated purpose doesn't match the reader's use (e.g. two different
  OAuth apps share a name), flag. Also: a scenario/knob the code added but the
  env template never lists.
- **Example:** `ZOOM_CLIENT_ID/SECRET` documented as one app while the token
  tool needs a different app's creds.

## 6. Review/config prompt encodes a retired rule

A `.github/` review prompt, lint config, or CI doc still enforces a rule a new
ADR retired, so future runs re-enforce the replaced model.

- **Heuristic:** when an ADR retires a rule, grep `.github/`, CI, and prompt
  files for the old rule's wording.

## 7. Same claim duplicated across files, updated in only some

One fact is stated in N docs; the PR updated some copies and missed others.

- **Heuristic:** for each code fact updated in the diff's docs, grep the whole
  tree for other statements of the same fact and confirm all moved together.
  This is the "sweep" that stops findings dribbling out one file per round.

## Reporting

Group findings by class in the section body so the reader sees the *pattern*,
not just N isolated lines. Every inline finding still needs its own doc line +
contradicting code location.
