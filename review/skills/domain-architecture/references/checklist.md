# Checklist — Domain / Architecture / Team boundaries

Dimensions from taxonomy cats **1**, **2**, **15**. Severity hints: `[B]` often blocking · `[S]` suggestion · `[Q]` question.

## 1. Domain / model / language

- [ ] **Ubiquitous language** — Names/types match domain terms; no accidental synonyms on public APIs. `[B]` if conflicting public terms
- [ ] **Bounded context alignment** — Change stays in owning context; no foreign concept leak. `[B]` if cross-context merge
- [ ] **Aggregate boundaries & invariants** — Invariants inside aggregate/transaction boundary. `[B]`
- [ ] **Entities vs value objects** — Identity vs equality; immutability where expected. `[S]`
- [ ] **Domain events** — Past-tense facts; sufficient payload; consumers don't invent alternate truths. `[B]` if contract breaks
- [ ] **Application vs domain vs infrastructure** — Domain logic not in controllers/repos/UI. `[B]` for significant logic in wrong layer
- [ ] **Anti-corruption layer** — External DTOs translated at boundary. `[B]` if foreign model becomes internal SoT
- [ ] **Context mapping** — Partnership / customer-supplier / conformist / ACL / shared kernel chosen consciously. `[Q]`/`[S]`
- [ ] **Domain rules vs policy knobs** — Rules as code/tests, not only PR folklore. `[S]`
- [ ] **Language consistency in tests/docs** — Specs speak the same language. `[S]`

## 2. Architecture & dependency rules

- [ ] **Dependency direction** — Inner layers don't depend on outer. `[B]`
- [ ] **Ports & adapters** — New I/O behind interfaces. `[B]` for hard DB coupling in core
- [ ] **Layering / package structure** — Correct module; no utility dumping ground. `[S]`
- [ ] **Coupling** — No new cycles/hard coupling across ownership. `[B]`
- [ ] **Cohesion** — Modules change for one reason. `[S]`
- [ ] **Use-case completeness** — Happy + failure modes owned by application service. `[S]`
- [ ] **Frameworks as details** — Framework types not deep in domain. `[S]`
- [ ] **Shared kernels / libraries** — New shared code justified. `[Q]`
- [ ] **Architecture fitness** — Matches established patterns or explains divergence. `[B]` if silent
- [ ] **Blast radius / integration surface** — Cross-service calls, queues, schemas, flags documented. `[B]` if undeclared

## 15. Team / org boundaries

- [ ] **Code ownership** — Right OWNERS/reviewers; owning team LGTM. `[B]`
- [ ] **Cross-team coupling** — New hard deps called out; prefer systemic fix over silent coupling. `[S]`/`[B]`
- [ ] **Platform vs product** — No leaky abstractions forcing every team to know internals. `[S]`
- [ ] **API as team contract** — Breaking changes negotiated; consumers notified. `[B]`
- [ ] **Cognitive load** — Too many domains in one service? `[Q]`
- [ ] **Interaction mode** — Collaboration vs X-as-a-Service mismatch. `[Q]`
- [ ] **Knowledge bus factor** — Needs pairing/docs if only author understands. `[S]`

## Clean Code (cat 3) — blocking overlay

- [ ] Silent failure / swallowed errors on domain-critical paths → **Blocker**
- [ ] Shared mutable state crossing boundaries → **Blocker**
- [ ] Layering violations (SQL in controllers, HTTP in domain) → **Blocker**
- [ ] Naming/style-only issues → Suggestion/Nit, not Blocker
