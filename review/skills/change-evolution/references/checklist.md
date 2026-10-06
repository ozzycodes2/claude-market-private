# Checklist — Change / CD / design quality

Dimensions from taxonomy categories **5 Change & evolution** and **4 Design quality**.

## 5. Change & evolution (CD readiness)

- [ ] **Incremental deliverability** — Each merge leaves system releasable. `issue (blocking)` if intermediate broken states required
- [ ] **Feature flags / dark launch** — Incomplete features safely off; cleanup plan. `suggestion (non-blocking)`/`issue (blocking)` for risky on-by-default
- [ ] **Trunk-based implications** — Long-lived branch risk; staleness. `suggestion (non-blocking)`
- [ ] **Feedback loops** — CI meaningful; failing tests not ignored. `issue (blocking)` if CI red/ignored
- [ ] **Reversibility** — Easy rollback; expand/contract for migrations. `issue (blocking)` for irreversible data loss without safeguards
- [ ] **Separating refactor from behavior** — Don't mix in one huge PR. `suggestion (non-blocking)`/`issue (blocking)` if huge mixed PR
- [ ] **Evolutionary path** — Parallel run, strangler, dual-write called out. `issue (blocking)` when the PR replaces a system; `question` otherwise
- [ ] **Config vs code change ordering** — Safe deploy order. `issue (blocking)` if wrong order can outage
- [ ] **Experiment / kill switch** — For uncertain bets. `suggestion (non-blocking)`

## 4. Design quality

These block regardless of module reach — a leaf module today is a shared module
next quarter. Blast radius sets `critical` vs `high`, not blocking vs not. Name
the resolving refactoring in `suggestion`.

- [ ] **Complexity budget** — Accidental vs essential; reader can grasp quickly. `issue (blocking)` · Extract Function, Decompose Conditional
- [ ] **Deep modules** — Simple interface, nontrivial implementation; avoid shallow class explosion. `issue (blocking)` · Inline Class, Combine Functions into Class
- [ ] **Information hiding** — Internals not leaked; stable abstractions at boundaries. `issue (blocking)` · Encapsulate Record, Encapsulate Collection, Hide Delegate
- [ ] **Abstraction level consistency** — Mixed high/low in one function. `issue (blocking)` · Extract Function
- [ ] **SOLID where useful** — Applied to real pain, not cargo-cult. `suggestion (non-blocking)`
- [ ] **YAGNI / speculative generality** — Don't solve imaginary futures. `issue (blocking)` · Inline Function, Collapse Hierarchy, Remove Dead Code, Change Function Declaration
- [ ] **KISS** — Simplest design that works and stays changeable. `suggestion (non-blocking)`
- [ ] **API of a module** — Hard to misuse; defaults safe. `issue (blocking)` · Introduce Parameter Object, Replace Constructor with Factory Function
- [ ] **Temporal coupling** — Must-call-in-order APIs without enforcement. `issue (blocking)` · Combine Functions into Transform; encapsulate the sequence behind one call
- [ ] **Feature envy / inappropriate intimacy** — Cross-module poking at internals. `issue (blocking)` · Move Function, Move Field, Hide Delegate
- [ ] **Primitive obsession vs modeling** — Missing domain types. `issue (blocking)` · Replace Primitive with Object, Introduce Parameter Object
- [ ] **Continuation of design debt** — Improves or degrades system design health? `issue (blocking)` if net degradation without plan

Where the language's idiom diverges from the catalog's OO move — enum over
hierarchy, `Option` over Null Object, newtype over wrapper class — prescribe the
idiom and say so. Add no trait, generic, or indirection the smell does not demand.

## Process / PR hygiene

- [ ] **Size** — Unreviewable mega-PR → request split. `issue (blocking)`
- [ ] **One concern** — Feature XOR refactor XOR dep bump. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Description map** — Why / risks / alternatives / systems affected. `issue (blocking)` if empty, or if present but missing *why*, on a non-trivial PR

## Clean Code (category 3 Code craft) — blocking overlay

- [ ] Dead/commented-out code masking intent → **Blocker** · Remove Dead Code
- [ ] Harmful duplication that will drift under parallel evolution → **high**/Blocker · Extract Function, Substitute Algorithm
- [ ] Pure naming/style with no domain-language conflict → Nit/Suggestion only
