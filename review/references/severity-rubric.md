# Severity Rubric (Conventional Comments)

Maps review severities to Conventional Comments labels/decorations and merge guidance.
Aligns with Google “Nit:”, Microsoft scope discipline, and the principal-engineer taxonomy.

| Severity (JSON) | Conventional Comments | Merge rule | When to use |
|---|---|---|---|
| **critical** | `issue (blocking)` — Blocker | Must resolve or explicitly accept risk with owner | Correctness, security, data loss, broken invariant, non-releasable CI, unsafe concurrency, breaking contract without plan, missing critical tests on risky change |
| **high** | `issue (blocking)` or `suggestion (blocking)` when cheap — Should-fix | Prefer fix in PR; allow follow-up if PE agrees & risk mitigated | Likely defect or significant maintainability/ops risk |
| **medium** | `suggestion (non-blocking)` | Optional; author judgment | Better design/readability/perf; alternative approach |
| *(as label)* | `question` | Answer before merge if it could be a blocker | Missing context; possible issue unsure |
| *(as label)* | `nitpick` / `chore` — Nit | Non-blocking; ideally automated | Style, minor consistency, process checklist |
| *(as label)* | `thought` / `note` | Non-blocking | Future design, mentoring, cross-team idea |
| *(as label)* | `praise` | N/A | Reinforce good practice |

## Clean Code (taxonomy cat 3) — blocking policy

Clean Code findings are **not** deferred to nits by default.

Treat as **Blocker / critical or high** when the craft issue hits:

- **Correctness** — silent failure, swallowed errors, wrong null/Optional policy on a real path
- **Invariants** — side effects that break shared mutable state; logging PII; dead code that masks intent
- **Maintainability on shared/hot paths** — unreadable nesting, boolean blindness, or duplication that will force every future change through the same footgun in a module many teams touch

Treat as **Suggestion / Nit** when:

- Naming/style preference without domain conflict
- Formatting that belongs in a linter
- Local/throwaway code with no shared consumers
- Equally valid alternate structure (do not block on preference)

## Decision heuristic

1. If wrong → users lose money/data/trust/security → **critical**
2. If wrong → outage / hard rollback / amplifying failure → **critical**
3. If wrong → next change is painful but system works → **medium** (or **high** if hot/shared module)
4. If preference without principle → **nitpick** or omit
5. If unclear → **question**, not blocker

**Google standard overlay:** Approve when the PR **improves code health** even if imperfect. Do not recreate perfectionism.

## Finding field defaults

Omit `label`/`decoration` to accept severity-derived defaults:

- `critical` / `high` → `issue` + `blocking`
- `medium` → `suggestion` + `non-blocking`
- `low` (if used) → `nitpick` + `non-blocking`

Override only when needed (e.g. `label: "question"` when unsure).
