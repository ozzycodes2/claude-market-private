# Severity Rubric (Conventional Comments)

Maps review severities to Conventional Comments labels/decorations and merge guidance.
Aligns with Google “Nit:”, Microsoft scope discipline, and the quality-review taxonomy.

| Severity (JSON) | Conventional Comments | Merge rule | When to use |
|---|---|---|---|
| **critical** | `issue (blocking)` — Blocker | Must resolve or explicitly accept risk with owner | Correctness, security, data loss, broken invariant, non-releasable CI, unsafe concurrency, breaking contract without plan, missing critical tests on risky change |
| **high** | `issue (blocking)` or `suggestion (blocking)` when cheap — Should-fix | Prefer fix in PR; allow follow-up if QR agrees & risk mitigated | Likely defect or significant maintainability/ops risk |
| **medium** | `suggestion (non-blocking)` | Optional; author judgment | Better design/readability/perf; alternative approach |
| *(as label)* | `question` | Answer before merge if it could be a blocker | Missing context; possible issue unsure |
| *(as label)* | `nitpick` / `chore` — Nit | Non-blocking; ideally automated | Style, minor consistency, process checklist |
| *(as label)* | `thought` / `note` | Non-blocking | Future design, mentoring, cross-team idea |
| *(as label)* | `praise` | N/A | Reinforce good practice |

## Clean Code & design quality (categories 3 and 4) — blocking policy

Craft and design findings are **not** deferred to nits, and **not** exempted by
module reach. A leaf module today is a shared module next quarter; "no shared
consumers yet" is how craft debt becomes permanent.

Treat as **Blocker / critical or high** when the finding hits:

- **Correctness** — silent failure, swallowed errors, wrong null/Optional policy on a real path
- **Invariants** — side effects that break shared mutable state; logging PII; dead code that masks intent
- **Maintainability** — unreadable nesting, boolean blindness, or duplication that forces every future change through the same footgun
- **Design quality** — the category 4 dimensions: complexity budget, deep modules, information hiding, abstraction-level consistency, misuse-prone API, temporal coupling, feature envy, primitive obsession

Blast radius sets **critical vs. high**. It does not set **blocking vs. not**.

For a design or craft finding, name the smell and the refactoring that resolves
it (Fowler, *Refactoring*; Kerievsky, *Refactoring to Patterns*). Where the
language's idiom diverges from the catalog's OO move — enum over hierarchy,
`Option` over Null Object, newtype over wrapper class — prescribe the idiom and
say so. Add no trait, generic, or indirection the smell does not demand.

Treat as **Suggestion / Nit** when:

- Naming/style preference with no domain-language conflict
- Formatting that belongs in a linter
- Equally valid alternate structure (do not block on preference)
- SOLID or KISS asserted without a concrete pain to point at

## Decision heuristic

1. If wrong → users lose money/data/trust/security → **critical**
2. If wrong → outage / hard rollback / amplifying failure → **critical**
3. If wrong → next change is painful but system works → **high**, blocking
4. If preference without principle → **nitpick** or omit
5. If unclear → **question**, not blocker

**Google standard overlay:** the bar is whether the PR improves code health, and
a named smell with a known refactoring is not perfectionism. Block on it, then
approve once resolved. Do not block on preference.

## Finding field defaults

Omit `label`/`decoration` to accept severity-derived defaults:

- `critical` / `high` → `issue` + `blocking`
- `medium` → `suggestion` + `non-blocking`
- `low` (if used) → `nitpick` + `non-blocking`

Override only when needed (e.g. `label: "question"` when unsure).
