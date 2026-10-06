# Checklist — Domain / Architecture / Team boundaries

Dimensions from taxonomy categories **1 Domain**, **2 Architecture**, **15 Team / org boundaries**. Severity hints: `issue (blocking)` · `suggestion (non-blocking)` · `question`.

## 1. Domain / model / language

- [ ] **Ubiquitous language** — Names/types match domain terms; no accidental synonyms on public APIs. `issue (blocking)` if conflicting public terms
- [ ] **Bounded context alignment** — Change stays in owning context; no foreign concept leak. `issue (blocking)` if cross-context merge
- [ ] **Aggregate boundaries & invariants** — Invariants inside aggregate/transaction boundary. `issue (blocking)`
- [ ] **Entities vs value objects** — Identity vs equality; immutability where expected. `issue (blocking)` — identity/equality errors are correctness
- [ ] **Domain events** — Past-tense facts; sufficient payload; consumers don't invent alternate truths. `issue (blocking)` if contract breaks
- [ ] **Application vs domain vs infrastructure** — Domain logic not in controllers/repos/UI. `issue (blocking)` for significant logic in wrong layer
- [ ] **Anti-corruption layer** — External DTOs translated at boundary. `issue (blocking)` if foreign model becomes internal SoT
- [ ] **Context mapping** — Partnership / customer-supplier / conformist / ACL / shared kernel chosen consciously. `question`/`suggestion (non-blocking)`
- [ ] **Domain rules vs policy knobs** — Rules as code/tests, not only PR folklore. `issue (blocking)` — a rule that lives only in a PR comment is undiscoverable
- [ ] **Language consistency in tests/docs** — Specs speak the same language. `issue (blocking)` for domain/public names; `nitpick` for test-local names

## 2. Architecture & dependency rules

- [ ] **Dependency direction** — Inner layers don't depend on outer. `issue (blocking)`
- [ ] **Ports & adapters** — New I/O behind interfaces. `issue (blocking)` for hard DB coupling in core
- [ ] **Layering / package structure** — Correct module; no utility dumping ground. `issue (blocking)` · Move Function, Extract Class
- [ ] **Coupling** — No new cycles/hard coupling across ownership. `issue (blocking)`
- [ ] **Cohesion** — Modules change for one reason. `issue (blocking)` — Divergent Change · Extract Class
- [ ] **Use-case completeness** — Happy + failure modes owned by application service. `issue (blocking)` — scattered error handling is a correctness risk
- [ ] **Frameworks as details** — Framework types not deep in domain. `issue (blocking)` · Extract Interface
- [ ] **Shared kernels / libraries** — New shared code justified. `issue (blocking)` without a named owner; `question` otherwise
- [ ] **Architecture fitness** — Matches established patterns or explains divergence. `issue (blocking)` if silent
- [ ] **Blast radius / integration surface** — Cross-service calls, queues, schemas, flags documented. `issue (blocking)` if undeclared

## 15. Team / org boundaries

- [ ] **Code ownership** — Right OWNERS/reviewers; owning team LGTM. `issue (blocking)`
- [ ] **Cross-team coupling** — New hard deps called out; prefer systemic fix over silent coupling. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Platform vs product** — No leaky abstractions forcing every team to know internals. `issue (blocking)`
- [ ] **API as team contract** — Breaking changes negotiated; consumers notified. `issue (blocking)`
- [ ] **Cognitive load** — Too many domains in one service? `question`
- [ ] **Interaction mode** — Collaboration vs X-as-a-Service mismatch. `question`
- [ ] **Knowledge bus factor** — Needs pairing/docs if only author understands. `suggestion (non-blocking)`

## Clean Code (category 3 Code craft) — blocking overlay

- [ ] Silent failure / swallowed errors on domain-critical paths → **Blocker**
- [ ] Shared mutable state crossing boundaries → **Blocker** · Encapsulate Variable, Inline Singleton
- [ ] Layering violations (SQL in controllers, HTTP in domain) → **Blocker** · Move Function
- [ ] God class / god service growth → **Blocker** · Extract Class
- [ ] Accidental synonyms for one concept (`User`/`Account`/`Customer`) → **Blocker** · Rename Field, Change Function Declaration
- [ ] Domain logic buried in controllers/repos/UI → **Blocker** · Move Function, Extract Function
- [ ] Foreign/legacy DTOs as internal source of truth → **Blocker** · Extract Class, Unify Interfaces with Adapter
- [ ] Naming/style-only issues with no domain-language conflict → Suggestion/Nit, not Blocker
