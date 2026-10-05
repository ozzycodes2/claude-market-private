# Quality Review PR Review Agent — Exhaustive Taxonomy (Prior Art)

Research date: 2026-10-01 (America/New_York). Citations are real public URLs or clearly labeled practice-derived / synthesis. No fabricated quotes.

---

## Peer-company / industry analogs (primary sources)

| Org / framework | What it structures | URL |
|---|---|---|
| Google Eng Practices — What to look for | Design, functionality, complexity/over-engineering, tests, naming, comments, style, consistency, documentation, every line, context, praise | https://google.github.io/eng-practices/review/reviewer/looking-for.html |
| Google Eng Practices — Standard of Code Review | Improve code health; approve when better even if imperfect; continuous improvement | https://google.github.io/eng-practices/review/reviewer/standard.html |
| Google Eng Practices — Small CLs | Size, atomicity, stacking, split refactor vs behavior, tests in same CL | https://google.github.io/eng-practices/review/developer/small-cls.html |
| Software Engineering at Google (SWE book) Ch.9 | ~200 LOC guideline, review within ~1 business day, small focused changes | https://abseil.io/resources/swe-book/html/ch09.html |
| Microsoft Code-with-Engineering Playbook | Human focus on business logic, tests, design/readability; security/PII; nits; scope discipline | https://microsoft.github.io/code-with-engineering-playbook/code-reviews/process-guidance/reviewer-guidance/ |
| Shopify Engineering | Small PRs (~200–300 LOC guideline), Draft/WIP for direction, one concern per PR, PR “map” (why/risks/alternatives), right reviewers | https://shopify.engineering/great-code-reviews |
| Palantir Code Review Best Practices | Scope (~5 files / ~20 min review), refactor≠behavior, deps scrutiny, security, actionable labels (suggestion vs required), knowledge sharing | https://blog.palantir.com/code-review-best-practices-19e02780015f |
| Meta (Facebook) Engineering | Every diff reviewed; stacked diffs; ownership-aware reviewers; review latency tooling | https://engineering.fb.com/2022/11/16/culture/meta-code-review-time-improving/ ; workflow/stacks: https://developers.facebook.com/blog/post/2022/11/15/meta-developers-workflow-exploring-tools-used-to-code/ |
| Phabricator “Writing Reviewable Code” (Meta-adjacent practice) | One idea ↔ one commit; explain *why* | https://secure.phabricator.com/book/phabflavor/article/writing_reviewable_code/ |
| Conventional Comments | Labels (praise/nitpick/suggestion/issue/todo/question/thought/chore/note) + (blocking)/(non-blocking)/(if-minor) | https://conventionalcomments.org/ |
| The Pragmatic Engineer (Gergely Orosz) | Good vs better reviews: contextual/system pass, maintainability, tone, nits→tooling, cross-team deps as org smell | https://blog.pragmaticengineer.com/good-code-reviews-better-code-reviews/ |
| OWASP Secure Code Review Cheat Sheet | Diff-based security review: authn/z, injection, crypto, business logic, data flow, secrets, config | https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html |
| OWASP ASVS / Code Review Guide | Verification levels & deeper checklist (use as security dimension catalog) | https://owasp.org/www-project-application-security-verification-standard/ ; Code Review Guide PDF: https://owasp.org/www-project-code-review-guide/ |
| Stripe API versioning | Backward compat, dated rolling versions, encapsulate breaking changes, API review process | https://stripe.com/blog/api-versioning |
| Netflix Tech Blog (resilience) | Timeouts, isolation, circuit breakers, fallbacks, retries only when safe | https://netflixtechblog.com/making-the-netflix-api-more-resilient-a8ec62159c2d ; https://netflixtechblog.com/fault-tolerance-in-a-high-volume-distributed-system-91ab4faae74a |
| Google SRE Book | Golden signals, SLOs/error budgets, production readiness themes | https://sre.google/sre-book/monitoring-distributed-systems/ ; https://sre.google/workbook/implementing-slos/ |

**Not found as a single public “Amazon code review checklist”** comparable to Google’s guide. Amazon “Bar Raiser” is primarily interview culture; do **not** cite as a formal PR-review taxonomy. Treat Amazon-flavored dimensions (ownership, operational readiness, customer impact, reversible decisions) as **practice-derived / synthesis**, not primary Amazon docs.

**Thoughtworks Technology Radar**: useful for technique adoption signals, not a fixed PR checklist. Thoughtworks has commentary on modernizing review (e.g. https://www.thoughtworks.com/en-us/insights/blog/testing/code-review-dead-long-live-code-review) — treat as **directional**, not a dimension catalog.

---

## Literature map (books → categories they most inform)

| Source | Primary categories |
|---|---|
| Evans — Domain-Driven Design | 1 Domain, 15 Boundaries |
| Vernon / other DDD practice | Aggregates, events, context maps |
| Martin — Clean Code | 3 Craft, 16 Anti-patterns |
| Martin — Clean Architecture / Hexagonal (Cockburn) | 2 Architecture |
| Farley — Modern Software Engineering | 5 Change & CD, 6 Testing |
| Hunt/Thomas — The Pragmatic Programmer | 3 Craft, 4 Design, 13 DX, 14 Hygiene |
| Orosz — Pragmatic Engineer (blog/guidebook) | 14 Hygiene, prioritization, org support |
| Fowler — Refactoring; Patterns of Enterprise Application Architecture | 4 Design, 16 Anti-patterns, 7 Data access |
| Feathers — Working Effectively with Legacy Code | 6 Characterization tests, seams |
| Kleppmann — DDIA | 7 Data & consistency |
| Forsgren et al. — Accelerate | 5 Feedback loops, delivery metrics (review as gate, not delay) |
| Larson — Staff Engineer; Reilly — Staff Engineer’s Path | QR prioritization, influence, boundaries |
| Ousterhout — A Philosophy of Software Design | 4 Deep modules, complexity, info hiding |
| Nygard — Release It! | 8 Reliability patterns |
| Google SRE | 8 Operability, SLOs |
| Skelton/Pais — Team Topologies | 15 Team/org boundaries |
| Secure by Design / OWASP | 9 Security |
| API Design Patterns (JJ Geewax et al.) + Stripe practices | 11 API/contracts |
| Freeman/Pryce — GOOS; Meszaros — xUnit Test Patterns | 6 Testing |
| Beck — TDD; Fowler testing pyramid essays | 6 Testing strategy |

---

# TAXONOMY

Format: **Category → dimension → what to look for in a PR**

Severity hint key used inline (formatter labels): `issue (blocking)` · `suggestion (non-blocking)` · `question` · `nitpick (non-blocking)`

---

## 1. Domain / model / language
*Informed by: Evans DDD; Clean Architecture use cases; Google “does this belong here?”; Microsoft business-logic focus*

- **Ubiquitous language** — Names/types match domain terms used by product/domain experts; no accidental synonyms (`User` vs `Account` vs `Customer` meaning the same thing). `issue (blocking)` if new public API invents conflicting terms
- **Bounded context alignment** — Change stays inside the owning context; no leaking foreign concepts into the model. `issue (blocking)` if cross-context model merge
- **Aggregate boundaries & invariants** — Invariants enforced inside the aggregate/transaction boundary, not “eventually maybe” across aggregates without explicit design. `issue (blocking)`
- **Entities vs value objects** — Identity vs equality used correctly; value objects immutable where expected. `suggestion (non-blocking)`
- **Domain events** — Events named past-tense facts; payload carries what’s needed without dumping whole aggregates; consumers don’t invent alternate truths. `suggestion (non-blocking)` / `issue (blocking)` if event contract breaks
- **Application vs domain vs infrastructure** — Domain logic not buried in controllers/repos/UI; use-case orchestration clear. `issue (blocking)` for new significant logic in wrong layer
- **Anti-corruption layer** — External/legacy DTOs translated at boundary; foreign schemas not polluting core. `issue (blocking)` if foreign model becomes source of truth internally
- **Context mapping** — Partnership / customer-supplier / conformist / ACL / shared kernel / published language chosen consciously when touching integrations. `question`/`suggestion (non-blocking)`
- **Domain rules vs policy knobs** — Business rules as code/tests, not only tribal knowledge in PR comments. `suggestion (non-blocking)`
- **Inconsistency of language in tests/docs** — Specs and tests speak the same language as production code. `suggestion (non-blocking)`

---

## 2. Architecture & dependency rules
*Informed by: Clean Architecture; Hexagonal; Palantir dependency scrutiny; Google design; Orosz “better” contextual pass*

- **Dependency direction** — Inner layers don’t depend on outer (UI/DB/framework); dependencies point toward policies/use cases. `issue (blocking)`
- **Ports & adapters** — New I/O behind interfaces; swapping adapters shouldn’t rewrite domain. `suggestion (non-blocking)`/`issue (blocking)` for hard DB coupling in core
- **Layering / package structure** — Change placed in correct module; no “utility dumping ground” growth without ownership. `suggestion (non-blocking)`
- **Coupling** — Temporal, content, control, common, stamp coupling; unwanted fan-out; circular deps. `issue (blocking)` for new cycles/hard coupling across ownership
- **Cohesion** — Modules change for one reason; feature cohesion vs coincidental. `suggestion (non-blocking)`
- **Use-case completeness** — Happy path + failure modes owned by application service, not scattered. `suggestion (non-blocking)`
- **Frameworks as details** — Framework annotations/types not leaking deep into domain. `suggestion (non-blocking)`
- **Shared kernels / libraries** — New shared code justified; avoids premature platformization. `question` (Google: belong in library?)
- **Architecture fitness** — Change matches established patterns; if pattern-breaking, PR explains why. `issue (blocking)` if silent divergence
- **Blast radius / integration surface** — New cross-service calls, queues, schemas, feature flags documented. `issue (blocking)` if undeclared

---

## 3. Code craft (Clean Code / Pragmatic Programmer)
*Informed by: Clean Code; Pragmatic Programmer; Google naming/comments/style; Microsoft readability*

- **Naming** — Intention-revealing; length vs clarity; consistent vocabulary. `suggestion (non-blocking)`/`nitpick (non-blocking)`
- **Function size & single purpose** — Small, do one thing; avoid deep nesting. `suggestion (non-blocking)`
- **Argument lists** — Too many params → parameter object / redesign. `suggestion (non-blocking)` (MS: >3 is a smell)
- **Duplication (DRY vs coupling)** — Remove harmful dup; don’t abstract premature “almost same”. `suggestion (non-blocking)`
- **Comments** — Prefer clarity of code; comments explain *why* / constraints / non-obvious; delete lying comments. `suggestion (non-blocking)` (Google)
- **Dead / commented-out code** — Remove; no inventory of ghosts. `suggestion (non-blocking)`/`issue (blocking)` if masks intent
- **Magic numbers / strings** — Named constants or domain concepts. `nitpick (non-blocking)`/`suggestion (non-blocking)`
- **Error handling** — Explicit; don’t swallow; don’t use exceptions for control flow without convention; map to domain errors. `issue (blocking)` if silent failure on critical path
- **Null / Optional discipline** — Consistent null policy; avoid null returns when empty collections/Option fit. `suggestion (non-blocking)`
- **Boolean blindness / flag params** — Prefer explicit types/APIs over `doX(true, false, true)`. `suggestion (non-blocking)`
- **Side effects visibility** — Pure vs impure clear; surprise mutation flagged. `suggestion (non-blocking)`/`issue (blocking)` if shared mutable state
- **Logging as craft** — Useful, leveled, not noisy; no secrets/PII. `suggestion (non-blocking)`/`issue (blocking)` for PII
- **Idiomatic use of language/stdlib** — Prefer platform facilities over reinvention (Palantir library note). `suggestion (non-blocking)`
- **Formatting/style** — Defer to linters; humans don’t block on style. `nitpick (non-blocking)` → automate (Google/MS/Palantir/Orosz)

---

## 4. Design quality
*Informed by: Ousterhout; SOLID (selectively); YAGNI/KISS; Google complexity/over-engineering; Fowler*

- **Complexity budget** — Accidental vs essential; can a reader grasp quickly? (Google/Ousterhout) `issue (blocking)` if needless complexity on hot/shared path
- **Deep modules** — Simple interface, nontrivial implementation; avoid shallow class explosion. `suggestion (non-blocking)`
- **Information hiding** — Internals not leaked; stable abstractions at boundaries. `suggestion (non-blocking)`/`issue (blocking)`
- **Abstraction level consistency** — Mixed high/low level in one function. `suggestion (non-blocking)`
- **SOLID where useful** — SRP/OCP/LSP/ISP/DIP applied to real pain, not cargo-cult. `suggestion (non-blocking)`
- **YAGNI / speculative generality** — Google: don’t solve future imaginary problems. `issue (blocking)` for heavy over-engineering
- **KISS** — Simplest design that works and stays changeable. `suggestion (non-blocking)`
- **API of a module** — Hard to misuse; defaults safe (principle of least astonishment). `suggestion (non-blocking)`/`issue (blocking)`
- **Temporal coupling** — Must-call-in-order APIs without enforcement. `suggestion (non-blocking)`
- **Feature envy / inappropriate intimacy** — Cross-module poking at internals. `suggestion (non-blocking)`
- **Primitive obsession vs modeling** — Missing domain types. `suggestion (non-blocking)`
- **Continuation of design debt** — Does PR improve or degrade system design health? (Google standard) `issue (blocking)` if net degradation without plan

---

## 5. Change & evolution (CD readiness)
*Informed by: Farley MSE; Accelerate; Google small CLs; Shopify/Meta stacking; trunk-based practice*

- **Incremental deliverability** — Each merge leaves system releasable. `issue (blocking)` if intermediate broken states required
- **Feature flags / dark launch** — Incomplete features safely off; flag cleanup plan. `suggestion (non-blocking)`/`issue (blocking)` for risky incomplete behavior on by default
- **Trunk-based implications** — Long-lived branch risk; conflict/staleness. `suggestion (non-blocking)`
- **Feedback loops** — CI signals meaningful; failing tests not ignored; review not substituting for automation. `issue (blocking)` if CI red/ignored
- **Reversibility** — Easy rollback; expand/contract for migrations. `issue (blocking)` for irreversible data loss without safeguards
- **Separating refactor from behavior** — Palantir/Google/Shopify: don’t mix. `suggestion (non-blocking)`/`issue (blocking)` if huge mixed PR
- **Evolutionary path** — Parallel run, strangler, dual-write called out when replacing systems. `question`/`issue (blocking)`
- **Config vs code change ordering** — Safe order for deploy. `issue (blocking)` if wrong order can outage
- **Experiment / kill switch** — For uncertain product/tech bets. `suggestion (non-blocking)`

---

## 6. Testing strategy
*Informed by: GOOS; xUnit Test Patterns; Farley; Feathers; Google/MS tests guidance*

- **Right altitude (pyramid)** — Unit/integration/e2e balance; avoid ice-cream cone. `suggestion (non-blocking)`/`issue (blocking)` if only brittle e2e for core logic
- **Tests in same PR as code** — Google/MS/Palantir: no “tests next”. `issue (blocking)`
- **Behavior vs implementation coupling** — Tests assert outcomes; not overly brittle to structure. `suggestion (non-blocking)`
- **Edge cases & invariants** — Boundaries, empties, duplicates, clock, locale, concurrency. `issue (blocking)` for money/auth/data integrity gaps
- **Characterization tests** — For legacy: lock behavior before change (Feathers). `suggestion (non-blocking)`/`issue (blocking)` if risky legacy untouched
- **Contract / consumer-driven tests** — For APIs/events between services. `suggestion (non-blocking)`/`issue (blocking)` for breaking provider changes
- **Property / generative / fuzz** — Where combinatorial space huge. `suggestion (non-blocking)`
- **Flaky tests** — New flakiness is a defect; quarantine with ownership. `issue (blocking)`
- **Test data & determinism** — No order dependence; control time/random/network. `issue (blocking)` if non-deterministic
- **Doubles quality** — Mocks vs fakes; over-mocking smell; verify right interactions. `suggestion (non-blocking)`
- **Negative / failure-path tests** — Errors, timeouts, partial failure. `suggestion (non-blocking)`/`issue (blocking)` for reliability-critical
- **Security-relevant tests** — Authz deny paths, injection fixtures where applicable. `suggestion (non-blocking)`
- **Coverage as signal not goal** — Missing critical paths > vanity %. `question`
- **Performance/regression tests** — When change touches known hot path. `suggestion (non-blocking)`
- **Test readability** — Arrange-Act-Assert / Given-When-Then; tests as docs. `suggestion (non-blocking)`

---

## 7. Data & consistency
*Informed by: Kleppmann DDIA; Fowler enterprise patterns; Stripe idempotency practices (synthesis + Stripe versioning post)*

- **Schema design** — Types, nullability, constraints, indexes match access patterns. `issue (blocking)` if integrity gaps
- **Migrations** — Expand/contract; backward/forward compatible deploys; locking/long migrations risk. `issue (blocking)`
- **Transactional boundaries** — What commits together; avoid multi-resource “transactions” without saga/outbox. `issue (blocking)`
- **Idempotency** — Writes/handlers safe under retry/at-least-once. `issue (blocking)` for payments/fulfillment/side effects
- **Exactly-once illusions** — At-least-once + idempotent consumer preferred; document. `question`
- **Eventual consistency UX** — Stale reads, read-your-writes, conflict resolution. `suggestion (non-blocking)`/`issue (blocking)` if user-visible corruption risk
- **Caching** — TTL, invalidation, stampede, poison cache, consistency with source of truth. `suggestion (non-blocking)`/`issue (blocking)`
- **Data retention / deletion** — GDPR-ish delete paths; soft-delete semantics. `issue (blocking)` for privacy requirements
- **Serialization compatibility** — Protobuf/JSON/Avro evolution rules. `issue (blocking)`
- **PII storage minimization** — Store only what’s needed; tokenization. `issue (blocking)`
- **Backfills** — Rate limits, observability, resume, correctness checks. `suggestion (non-blocking)`/`issue (blocking)`
- **Dual-write hazards** — Two stores updated; failure modes. `issue (blocking)` without outbox/CDC plan

---

## 8. Reliability & operability
*Informed by: Release It!; Google SRE; Netflix resilience blogs*

- **Failure modes** — What happens when dependency down/slow/wrong? `issue (blocking)` for new critical path deps without plan
- **Timeouts** — Explicit, bounded, consistent with SLOs; no infinite hangs. `issue (blocking)`
- **Retries** — Only idempotent; backoff + jitter; retry budget; single retry layer (avoid storms). `issue (blocking)` if blind retry on non-idempotent
- **Circuit breakers / bulkheads** — Isolation of failure; fallbacks. `suggestion (non-blocking)`/`issue (blocking)` for high-fanout services
- **Load shedding / backpressure** — Queue bounds; reject vs absorb. `suggestion (non-blocking)`
- **Graceful degradation** — Partial functionality over total failure. `suggestion (non-blocking)`
- **Observability** — Logs/metrics/traces for new paths; golden signals (latency, traffic, errors, saturation). `issue (blocking)` if new user-critical path is dark
- **SLOs / error budget awareness** — Change risk vs burn. `question` for high-risk
- **Alerting** — Actionable alerts; not pages for symptoms that aren’t actionable. `suggestion (non-blocking)`
- **Runbooks / ops notes** — Deploy/rollback/feature-flag instructions when behavior changes ops. `suggestion (non-blocking)`/`issue (blocking)` for high-risk
- **Health checks** — Liveness vs readiness correct. `suggestion (non-blocking)`
- **Resource limits** — Memory/CPU/FD/connection pools; DoS amplification. `issue (blocking)` if unbounded
- **Crash-only / restart safety** — Process can die mid-op safely (idempotent + durable state). `suggestion (non-blocking)`
- **Time & clocks** — Skew, DST, monotonic vs wall clock. `suggestion (non-blocking)`/`issue (blocking)` for scheduling/billing

---

## 9. Security & privacy
*Informed by: OWASP cheat sheet/ASVS/Top 10; Microsoft PII notes; Palantir security section; Secure by Design*

- **Threat modeling lite** — New trust boundaries, assets, attackers (STRIDE-ish). `question`/`issue (blocking)` for high-risk features
- **Authentication** — Session/token handling; password storage; MFA touchpoints. `issue (blocking)`
- **Authorization** — Server-side; default deny; IDOR; function-level authz; central checks. `issue (blocking)`
- **Injection** — SQL/NoSQL/OS/LDAP/template; parameterized queries; path traversal. `issue (blocking)`
- **XSS / output encoding** — Context-appropriate encoding. `issue (blocking)` for web
- **SSRF / unsafe egress** — User-controlled URLs. `issue (blocking)`
- **Deserialization / XXE** — Untrusted data. `issue (blocking)`
- **Secrets management** — No hardcoded secrets; rotation; secret scanning. `issue (blocking)`
- **Cryptography** — Modern algs; key management; no home-rolled crypto. `issue (blocking)`
- **PII / logging** — No PII in logs/metrics/traces/exception messages (MS EUII). `issue (blocking)`
- **Privacy controls** — Consent, retention, access, deletion hooks. `issue (blocking)` when in scope
- **Security headers / TLS / cookie flags** — When touching HTTP edge. `suggestion (non-blocking)`/`issue (blocking)`
- **Dependency CVEs** — New deps reviewed; pin/lockfiles. `suggestion (non-blocking)`/`issue (blocking)` for known critical
- **Abuse / rate limits** — Expensive endpoints protected. `suggestion (non-blocking)`/`issue (blocking)`
- **Supply chain** — CI permissions, artifact provenance (practice-derived). `suggestion (non-blocking)`
- **Business logic abuse** — Workflow bypass, race to privilege (OWASP). `issue (blocking)`

---

## 10. Performance & scalability
*Informed by: DDIA; Release It!; Google functionality/complexity; MS N+1 note*

- **Hot paths** — Algorithmic complexity on critical request/job paths. `issue (blocking)` if obvious O(n²) on large n
- **N+1 queries / chatty I/O** — Batching, joins, data loaders. `issue (blocking)`/`suggestion (non-blocking)` by severity
- **Pagination / unbounded result sets** — Limits enforced. `issue (blocking)`
- **Caching strategy** — Correctness + hit rate; stampede. `suggestion (non-blocking)`
- **Allocation / GC pressure** — Hot loops. `suggestion (non-blocking)`
- **Concurrency for scale** — Parallelism vs complexity tradeoff. `question`
- **Data volume assumptions** — Documented expected sizes; tested near limits. `suggestion (non-blocking)`
- **Fan-out amplification** — One request → N downstream. `issue (blocking)` if uncontrolled
- **Async offload** — Slow work not on request thread without reason. `suggestion (non-blocking)`
- **Capacity / cost** — New storage/compute cost called out. `question`/`suggestion (non-blocking)`

---

## 11. API / contract design
*Informed by: Stripe versioning; API Design Patterns; Google “users of the code”; Palantir backward compat*

- **Backward compatibility** — Additive preferred; no silent renames/type changes. `issue (blocking)`
- **Versioning strategy** — Explicit; Stripe-like encapsulation of breaks when needed. `issue (blocking)` if break without version story
- **Error shapes** — Stable codes/messages; actionable; no sensitive leak. `suggestion (non-blocking)`/`issue (blocking)`
- **Idempotency keys** — For mutating public APIs. `issue (blocking)` for payment-like APIs
- **Pagination/filtering/sorting contracts** — Consistent, documented. `suggestion (non-blocking)`
- **Pagination tokens vs offset** — Stability under concurrent writes. `suggestion (non-blocking)`
- **Authn/z at API boundary** — Consistent with codebase (Palantir). `issue (blocking)`
- **Payload minimization** — Don’t over-expose fields. `suggestion (non-blocking)`/`issue (blocking)` privacy
- **Event / webhook contracts** — Signature verification, versioning, at-least-once. `issue (blocking)`
- **Client SDK impact** — Generated clients / breaking field changes. `suggestion (non-blocking)`
- **Deprecation policy** — Timeline, dual-run, docs. `suggestion (non-blocking)`/`issue (blocking)`
- **HATEOAS/resource modeling** — Consistency with existing API style. `suggestion (non-blocking)`
- **Public vs internal API** — Different stability bars. `question`

---

## 12. Concurrency & correctness
*Informed by: Google parallel programming guidance; OWASP race/TOCTOU; Feathers; systems lit*

- **Race conditions** — Shared mutable state; check-then-act. `issue (blocking)`
- **Deadlocks / lock ordering** — Documented lock hierarchy. `issue (blocking)`
- **Atomicity** — Compare-and-swap / transactions / DB constraints for invariants. `issue (blocking)`
- **Memory model / visibility** — Cross-thread publication. `issue (blocking)` when applicable
- **Async correctness** — Cancellation, structured concurrency, lost wakeups. `suggestion (non-blocking)`/`issue (blocking)`
- **Idempotent handlers under concurrency** — Unique constraints as safety net. `issue (blocking)`
- **Time-of-check/time-of-use** — Filesystem/authz races. `issue (blocking)`
- **Ordering guarantees** — Queue/partition assumptions stated. `question`
- **Poison messages / DLQ** — Failure isolation. `suggestion (non-blocking)`

---

## 13. Developer experience of the change
*Informed by: Pragmatic Programmer; Google docs; Shopify PR map; Palantir maintainability*

- **Local understandability** — Can a teammate grasp without author? `suggestion (non-blocking)`/`issue (blocking)` if impenetrable
- **Docs updates** — README, ADRs, runbooks, API refs when behavior/build/release changes (Google). `suggestion (non-blocking)`/`issue (blocking)`
- **Migration path for callers** — Examples, codemods, deprecation. `suggestion (non-blocking)`/`issue (blocking)` for breaking internal APIs
- **Tooling / DX** — Scripts, Makefile, IDE config, generators updated. `suggestion (non-blocking)`
- **Discoverability** — New module findable; ownership METADATA/CODEOWNERS. `suggestion (non-blocking)`
- **Examples & sample usage** — Especially for new libraries/APIs (Google: include usage with new API). `suggestion (non-blocking)`
- **Cognitive load** — Number of new concepts introduced justified. `suggestion (non-blocking)`
- **Onboarding impact** — Does this make the system harder for new joiners? (Orosz empathy) `suggestion (non-blocking)`

---

## 14. Process / PR hygiene
*Informed by: Google small CLs/descriptions; Shopify; Meta stacks; Phabricator why; Pragmatic Engineer; Conventional Comments; MS scope*

- **Size** — Prefer ~100–300 LOC conceptual change; reject/split mega-PRs (Google/Shopify/SWE book). `issue (blocking)` to request split when unreviewable
- **Atomicity / one concern** — Feature XOR refactor XOR dep bump (Shopify/Palantir). `suggestion (non-blocking)`/`issue (blocking)`
- **Description quality** — Why, who benefits, what could go wrong, alternatives considered, systems affected (Shopify). `issue (blocking)` if empty on non-trivial PR
- **Risk communication** — Rollout plan, monitoring, rollback. `issue (blocking)` for high-risk
- **Test plan evidence** — What was run; screenshots for UI (Google/MS). `suggestion (non-blocking)`/`issue (blocking)`
- **Linked issue / product intent** — Traceability. `suggestion (non-blocking)`
- **Stacking** — Meta/Google stacking for large work. `suggestion (non-blocking)`
- **Draft/WIP for design feedback** — Shopify early direction. `suggestion (non-blocking)`
- **Reviewer selection** — Owners + expertise + learners (Shopify/Google OWNERS). `suggestion (non-blocking)`
- **CI green** — Required checks pass before human deep review (Palantir). `issue (blocking)`
- **Commit message quality** — Imperative why (Palantir). `nitpick (non-blocking)`/`suggestion (non-blocking)`
- **No drive-by unrelated changes** — MS scope discipline. `suggestion (non-blocking)`
- **Comment taxonomy** — Conventional Comments labels + blocking decorations. `suggestion (non-blocking)` process for agent output

---

## 15. Team / org boundaries
*Informed by: Team Topologies; DDD context maps; Orosz cross-timezone deps; Meta ownership; Palantir coupling*

- **Code ownership** — Right OWNERS/reviewers; don’t merge without owning team LGTM. `issue (blocking)`
- **Cross-team coupling** — New hard deps creating review/latency bottlenecks (Orosz “better” systemic fix). `suggestion (non-blocking)`/`issue (blocking)`
- **Platform vs product responsibilities** — Leaky abstractions forcing every team to know internals. `suggestion (non-blocking)`
- **API as team contract** — Changes negotiated; consumer notification. `issue (blocking)` for breaking
- **Cognitive load on team** — Too many domains in one service (Team Topologies). `question`
- **Interaction mode** — Collaboration vs X-as-a-Service vs facilitating — implicit mode mismatch. `question`
- **Knowledge bus factor** — Only author understands; needs pairing/docs. `suggestion (non-blocking)`

---

## 16. Anti-patterns to flag (explicit library for the agent)
*Synthesis from Fowler, Clean Code, Google over-engineering, Release It!, OWASP, review guides*

**Design / code**
- God class / god service
- Anemic domain model where rich domain was expected (or vice versa without reason)
- Shotgun surgery / divergent change signals
- Copy-paste with drift
- Speculative generality / gold plating
- Boolean flag parameters proliferating
- Catch-all `Exception` / empty catch
- Returning null instead of empty / Optional inconsistency
- Leaking abstractions (ORM entities as API DTOs)
- Shared mutable global/singleton state
- Circular dependencies
- Layering violations (SQL in controllers, HTTP in domain)

**Process**
- PR too large / multiple concerns
- Refactor mixed with feature
- “Tests follow-up” promise
- Style debates that belong in linters
- Blocking on pure preference nits
- Approval without reading (rubber stamp)
- Scope creep comments blocking unrelated debt

**Data / distributed**
- Dual writes without outbox
- Non-idempotent retries
- Unbounded queries/queues
- Distributed monolith chatty sync calls on critical path
- Ignoring poison messages

**Security**
- Client-trusted authorization/prices/roles
- String-built queries
- Secrets in repo/logs
- Debug endpoints left on
- Overly permissive CORS / authz

**Reliability**
- Missing timeouts
- Retry storms
- Cascading failure without isolation
- Silent swallowing of errors
- Metrics without SLOs / alert spam

---

# What a Quality Review prioritizes vs junior over-index

## QR / Staff-style priority stack (review order)
1. **Intent & necessity** — Is this the right problem? Should it exist? (Shopify: sometimes best outcome is don’t merge)
2. **System fit & architecture** — Boundaries, dependency direction, ownership, blast radius
3. **Correctness of domain & invariants** — Especially money, authz, data integrity, concurrency
4. **Failure behavior & operability** — Timeouts, idempotency, observability, rollback
5. **Contracts** — API/event/schema compatibility & migration safety
6. **Test strategy adequacy** — Right tests proving the riskiest behaviors
7. **Design simplicity** — Deep modules, YAGNI, complexity budget
8. **Security/privacy on trust-boundary changes**
9. **Maintainability & DX** — Can the team evolve this?
10. **Craft details** — Naming, small cleanups — teach, don’t block unless they obscure correctness

## What juniors often over-index on (agent should de-emphasize as blockers)
- Formatting, import order, brace style, alphabetical lists → **linters/Nits**
- Preferring familiar patterns without system context
- Demanding perfect SOLID on throwaway/local code
- Line-by-line style without reading PR description/tests first
- Blocking on alternative implementations that are equally valid
- Expanding scope to adjacent tech debt (MS: file separate tasks)
- Excessive mocking dogma or coverage %-only gates
- Bike-shedding names when domain language is already clear enough

## QR “better review” behaviors (Orosz + Google + Palantir)
- Contextual pass after light pass
- Ask questions before asserting ignorance
- Separate **blocking** vs **non-blocking** explicitly (Conventional Comments)
- Praise good work (Google/Shopify)
- Escalate long debates to sync; don’t infinite-loop in comments
- Push repeated nits into tooling/standards
- Watch for organizational smells (wrong codebase, wrong ownership)

---

# Proposed severity rubric (for agent skill)

Align comments with Conventional Comments + Google “Nit:” + MS guidance.

| Severity | When to use | Merge rule | Examples |
|---|---|---|---|
| **Blocker (issue/todo blocking)** | Correctness, security, data loss, broken invariant, non-releasable CI, unsafe concurrency, breaking contract without plan, missing critical tests on risky change | Must resolve or explicitly accept risk with owner | Authz hole; non-idempotent payment retry; migration that locks prod; silent catch on financial path |
| **Should-fix (suggestion blocking if cheap / issue non-blocking if costly)** | Likely defect or significant maintainability/ops risk; fix if in scope | Prefer fix in PR; allow follow-up issue if QR agrees & risk mitigated | Missing timeout; weak observability on new path; unclear aggregate boundary |
| **Suggestion (non-blocking)** | Better design/readability/perf; alternative approach | Optional; author judgment | Extract method; rename for ubiquitous language; cache |
| **Question** | Missing context; possible issue unsure | Answer before merge if it could be blocker | “Is dual-write intentional? What’s failure mode?” |
| **Nit / chore** | Style, minor consistency, process checklist | Non-blocking; ideally automated | Import order; changelog checkbox |
| **Thought / note** | Future design, mentoring, cross-team idea | Non-blocking | “Consider ACL when service B adopts this event” |
| **Praise** | Reinforce good practice | N/A | Clean expand/contract migration; excellent characterization tests |

**Agent decision heuristic**
- If wrong → users lose money/data/trust/security → **Blocker**
- If wrong → outage/hard rollback/amplifying failure → **Blocker**
- If wrong → next change is painful but system works → **Suggestion** (or should-fix if in hot shared module)
- If preference without principle → **Nit** or omit
- If unclear → **Question**, not Blocker

**Google standard overlay:** Approve when PR **improves code health** even if imperfect; don’t hold for perfection. QR agent should not recreate perfectionism.

---

# Suggested skill prompt skeleton (for authoring)

1. Read PR description + linked issue first; if map missing on non-trivial PR, request it before deep review.
2. Identify **risk class** (domain/auth/data/API/concurrency/ops).
3. Walk categories **1→2→7→8→9→11→12→6** before craft nits.
4. Emit Conventional Comments with severity decorations.
5. End with summary: blockers, residual risks, what looks strong, suggested follow-ups out of scope.
6. Never rubber-stamp generated/large PRs; never block solely on style.

---

# Gaps / honesty notes
- No single public Amazon “PR review checklist” found equivalent to Google eng-practices; Amazon themes included as synthesis only.
- Thoughtworks Radar is not a review rubric; cite sparingly as technique signals.
- Book principles above are from well-known published works; page-level quotes not invented—dimensions are practice distillations suitable for prompts.
