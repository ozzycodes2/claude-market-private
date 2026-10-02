# Checklist — Change / CD / design quality

Dimensions from taxonomy cats **5** and **4**.

## 5. Change & evolution (CD readiness)

- [ ] **Incremental deliverability** — Each merge leaves system releasable. `[B]` if intermediate broken states required
- [ ] **Feature flags / dark launch** — Incomplete features safely off; cleanup plan. `[S]`/`[B]` for risky on-by-default
- [ ] **Trunk-based implications** — Long-lived branch risk; staleness. `[S]`
- [ ] **Feedback loops** — CI meaningful; failing tests not ignored. `[B]` if CI red/ignored
- [ ] **Reversibility** — Easy rollback; expand/contract for migrations. `[B]` for irreversible data loss without safeguards
- [ ] **Separating refactor from behavior** — Don't mix in one huge PR. `[S]`/`[B]` if huge mixed PR
- [ ] **Evolutionary path** — Parallel run, strangler, dual-write called out. `[Q]`/`[B]`
- [ ] **Config vs code change ordering** — Safe deploy order. `[B]` if wrong order can outage
- [ ] **Experiment / kill switch** — For uncertain bets. `[S]`

## 4. Design quality

- [ ] **Complexity budget** — Accidental vs essential; reader can grasp quickly. `[B]` if needless complexity on hot/shared path
- [ ] **Deep modules** — Simple interface, nontrivial implementation; avoid shallow class explosion. `[S]`
- [ ] **Information hiding** — Internals not leaked; stable abstractions at boundaries. `[S]`/`[B]`
- [ ] **Abstraction level consistency** — Mixed high/low in one function. `[S]`
- [ ] **SOLID where useful** — Applied to real pain, not cargo-cult. `[S]`
- [ ] **YAGNI / speculative generality** — Don't solve imaginary futures. `[B]` for heavy over-engineering
- [ ] **KISS** — Simplest design that works and stays changeable. `[S]`
- [ ] **API of a module** — Hard to misuse; defaults safe. `[S]`/`[B]`
- [ ] **Temporal coupling** — Must-call-in-order APIs without enforcement. `[S]`
- [ ] **Feature envy / inappropriate intimacy** — Cross-module poking at internals. `[S]`
- [ ] **Primitive obsession vs modeling** — Missing domain types. `[S]`
- [ ] **Continuation of design debt** — Improves or degrades system design health? `[B]` if net degradation without plan

## Hygiene tie-ins (from analyze preflight)

- [ ] **Size** — Unreviewable mega-PR → request split. `[B]`
- [ ] **One concern** — Feature XOR refactor XOR dep bump. `[S]`/`[B]`
- [ ] **Description map** — Why / risks / alternatives / systems affected. `[B]` if empty on non-trivial PR

## Clean Code (cat 3) — blocking overlay

- [ ] Dead/commented-out code masking intent in evolving modules → **Blocker**
- [ ] Harmful duplication that will drift under parallel evolution on shared paths → **high**/Blocker
- [ ] Pure naming/style → Nit/Suggestion only
