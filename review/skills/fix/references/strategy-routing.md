# Strategy routing — which fix a finding gets

Every open finding routes to exactly one strategy. Evaluate top-down; **first
match wins.** Scope is all findings, so nothing is filtered out at intake — S6 is
how a finding with no mechanical remedy is handled honestly, not how the skill
narrows itself to the easy cases.

| | Strategy | Route when | Commit prefix |
|---|---|---|---|
| **S6** | Defer | the remedy names no action (`consider…`, `decide whether…`, `align with…`); or ≥2 defensible designs have different consequences; or it crosses a boundary this repo does not own; or `label == "question"`; or `kind == "design-decision"` | none |
| **S5** | Regenerate | `extra.drift_class == "rendered-lag"`, or `kind == "generated-artifact"` | `chore` |
| **S0** | Formatter | `kind == "lint"`, or `extra.fix_type ∈ {lint, formatting}` | one batch, `style` |
| **S2** | Repair | `kind ∈ {correctness, security, dependency}`, or the remedy changes observable behavior | `fix` |
| **S4** | Comment | `extra.drift_class == "stale-comment"`, or `kind == "code-comment"`, or `path` is source and the remedy targets a comment or docstring | `docs` |
| **S3** | Prose | `kind == "docs-prose"`, or `path` ends in `.md`/`.rst`/`.adoc`/`.txt` | `docs` |
| **S1** | Refactor | default for anything left where a catalog refactoring is named or derivable | `refactor` |

A finding matching nothing and carrying no `path` → **S6**, reason
`ambiguous-remedy`.

## Ordering

The order findings are worked in is load-bearing, not cosmetic.

1. **S5 first** for any path that S1, S3, or S4 also touch. Regeneration
   overwrites the whole artifact, so a hand edit applied first is silently
   reverted.
2. **S2 next** — correctness and security sit at positions 3-5 of the priority
   stack in `shared/quality-review-pr-review-taxonomy.md`.
3. **S3, S4, S0.**
4. **S1 last.** Where `can_run_safely` is false these commits are unverified, and
   at the tip of the branch an unwind is a single `git revert` rather than
   mid-history surgery. This also agrees with the priority stack, where design
   simplicity sits at 7.
5. **Within a sequential group, descending line number.** An edit lower in the
   file does not shift the lines above it, so earlier findings stay locatable.

## Partitioning for parallel work

- Group open findings by the **set of files** each requires.
- Disjoint file sets → one agent each, **all dispatched in a single message**.
- Any shared file → one agent handling those findings **sequentially**, re-reading
  the file between them.
- **Cap at 4 concurrent agents.** Not a safety limit — agents no longer commit —
  but the orchestrator serializes commits anyway, and more than four parallel
  editors in one worktree makes the end-of-run reconciliation unreadable.

## Model, pinned per strategy

Never omit `model`. An omitted `model` inherits the session model, which
collapses the intended split — the same trap documented in
`skills/review/SKILL.md` for the three bug-finder passes.

| Strategy | `subagent_type` | `model` | Why |
|---|---|---|---|
| S1, design-level (enum over hierarchy, typestate, newtype, module split) | `general-purpose` | `opus` | Picking the move and judging the idiom divergence is judgement; a wrong pick adds indirection that outlives the PR |
| S1, mechanical (Extract Function, Inline, Move, Remove Dead Code) | `general-purpose` | `sonnet` | The mechanics are deterministic once the move is chosen |
| S2 | `general-purpose` | `opus` | A behavior change on a correctness or security path |
| S3, S4 | `general-purpose` | `sonnet` | The prose rules are checkable; a smaller model under-edits |
| S5, S0, S6 | no agent | — | The orchestrator runs the recipe, runs the formatter, or records the deferral |

## S6 — the deferral criteria in full

Defer when any of these holds:

1. The remedy names no mechanical action — it asks a question, or says
   "consider", "decide whether", "align with the team".
2. Resolving it means choosing between two or more defensible designs with
   different consequences: outbox vs. change-data-capture vs. accepting the
   window; expand/contract vs. big-bang migration; an additive field vs. a
   version bump.
3. It crosses a boundary this repository does not own — another team's schema, an
   upstream bug, an external consumer's contract.
4. An agent returned `needs-decision` or `not-reproducible`.
5. No command resolves for S5 or S0 (`no-regen-command`, `no-lint-command`).
6. `path` is null and localization found zero, or more than three, candidate
   sites (`ambiguous-remedy`).

**A failing test is not on this list.** See the red-green rules in
`shared/fix-contract.md`: a test failure is iterated on, never deferred.

Record the deferral in the ledger with a `decision_needed` that a human can
answer without reading the rest of the review. A deferred finding gets **no edit
and no commit**, keeps its original severity, and never acquires a bare `TODO` as
a consolation prize — an untracked defect note is exactly what the comment rules
forbid.

## Known overlaps, and who wins

- **Lint fixes.** `codegen` drafts `lint_fixes[]` but cannot apply them: it never
  writes repository files and always sets `review_required: true`. Treat its
  drafts as *evidence that lint drift exists*, discard the diffs, and run the
  repo's own formatter — the tool is authoritative, and a diff drafted during
  review is stale by the time `fix` runs. One batch commit; N whitespace commits
  is noise.
- **Swallowed errors.** The catalog calls this Replace Error Code with Exception,
  which reads like a refactoring, but removing a swallowed error *changes
  observable behavior*. Route **S2**, not S1, and require a test.
- **Generated artifacts.** Anything `rendered-lag` is S5 even when it looks like
  prose. Hand-editing it is reverted by the next generator run.
