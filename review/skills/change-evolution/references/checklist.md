# Checklist — Change / CD / design quality

Dimensions from taxonomy categories **5 Change & evolution** and **4 Design quality**.

## 5. Change & evolution (CD readiness)

- [ ] **Incremental deliverability** — Each merge leaves system releasable. `issue (blocking)` if intermediate broken states required
- [ ] **Feature flags / dark launch** — Incomplete features safely off; cleanup plan. `suggestion (non-blocking)`/`issue (blocking)` for risky on-by-default
- [ ] **Trunk-based implications** — Long-lived branch risk; staleness. `suggestion (non-blocking)`
- [ ] **Feedback loops** — CI meaningful; failing tests not ignored. `issue (blocking)` if CI red/ignored
- [ ] **Reversibility** — Easy rollback; expand/contract for migrations. `issue (blocking)` for irreversible data loss without safeguards
- [ ] **Separating refactor from behavior** — Don't mix in one huge PR. `suggestion (non-blocking)`/`issue (blocking)` if huge mixed PR
- [ ] **Evolutionary path** — Parallel run, strangler, dual-write called out. `question`/`issue (blocking)`
- [ ] **Config vs code change ordering** — Safe deploy order. `issue (blocking)` if wrong order can outage
- [ ] **Experiment / kill switch** — For uncertain bets. `suggestion (non-blocking)`

## 4. Design quality

- [ ] **Complexity budget** — Accidental vs essential; reader can grasp quickly. `issue (blocking)` if needless complexity on hot/shared path
- [ ] **Deep modules** — Simple interface, nontrivial implementation; avoid shallow class explosion. `suggestion (non-blocking)`
- [ ] **Information hiding** — Internals not leaked; stable abstractions at boundaries. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Abstraction level consistency** — Mixed high/low in one function. `suggestion (non-blocking)`
- [ ] **SOLID where useful** — Applied to real pain, not cargo-cult. `suggestion (non-blocking)`
- [ ] **YAGNI / speculative generality** — Don't solve imaginary futures. `issue (blocking)` for heavy over-engineering
- [ ] **KISS** — Simplest design that works and stays changeable. `suggestion (non-blocking)`
- [ ] **API of a module** — Hard to misuse; defaults safe. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Temporal coupling** — Must-call-in-order APIs without enforcement. `suggestion (non-blocking)`
- [ ] **Feature envy / inappropriate intimacy** — Cross-module poking at internals. `suggestion (non-blocking)`
- [ ] **Primitive obsession vs modeling** — Missing domain types. `suggestion (non-blocking)`
- [ ] **Continuation of design debt** — Improves or degrades system design health? `issue (blocking)` if net degradation without plan

## Process / PR hygiene

- [ ] **Size** — Unreviewable mega-PR → request split. `issue (blocking)`
- [ ] **One concern** — Feature XOR refactor XOR dep bump. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Description map** — Why / risks / alternatives / systems affected. `issue (blocking)` if empty on non-trivial PR

## Clean Code (category 3 Code craft) — blocking overlay

- [ ] Dead/commented-out code masking intent in evolving modules → **Blocker**
- [ ] Harmful duplication that will drift under parallel evolution on shared paths → **high**/Blocker
- [ ] Pure naming/style → Nit/Suggestion only
