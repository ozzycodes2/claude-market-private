# Principal-Engineer PR Review Agent — Exhaustive Taxonomy (Prior Art)

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
| Larson — Staff Engineer; Reilly — Staff Engineer’s Path | PE prioritization, influence, boundaries |
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

Severity hint key used inline: `[B]` often blocking · `[S]` suggestion · `[Q]` question/clarify · `[N]` nit/tooling

---

## 1. Domain / model / language
*Informed by: Evans DDD; Clean Architecture use cases; Google “does this belong here?”; Microsoft business-logic focus*

- **Ubiquitous language** — Names/types match domain terms used by product/domain experts; no accidental synonyms (`User` vs `Account` vs `Customer` meaning the same thing). `[B]/` if new public API invents conflicting terms]
- **Bounded context alignment** — Change stays inside the owning context; no leaking foreign concepts into the model. `[B]` if cross-context model merge
- **Aggregate boundaries & invariants** — Invariants enforced inside the aggregate/transaction boundary, not “eventually maybe” across aggregates without explicit design. `[B]`
- **Entities vs value objects** — Identity vs equality used correctly; value objects immutable where expected. `[S]`
- **Domain events** — Events named past-tense facts; payload carries what’s needed without dumping whole aggregates; consumers don’t invent alternate truths. `[S]/` `[B]` if event contract breaks
- **Application vs domain vs infrastructure** — Domain logic not buried in controllers/repos/UI; use-case orchestration clear. `[B]` for new significant logic in wrong layer
- **Anti-corruption layer** — External/legacy DTOs translated at boundary; foreign schemas not polluting core. `[B]` if foreign model becomes source of truth internally
- **Context mapping** — Partnership / customer-supplier / conformist / ACL / shared kernel / published language chosen consciously when touching integrations. `[Q]`/`[S]`
- **Domain rules vs policy knobs** — Business rules as code/tests, not only tribal knowledge in PR comments. `[S]`
- **Inconsistency of language in tests/docs** — Specs and tests speak the same language as production code. `[S]`

---

## 2. Architecture & dependency rules
*Informed by: Clean Architecture; Hexagonal; Palantir dependency scrutiny; Google design; Orosz “better” contextual pass*

- **Dependency direction** — Inner layers don’t depend on outer (UI/DB/framework); dependencies point toward policies/use cases. `[B]`
- **Ports & adapters** — New I/O behind interfaces; swapping adapters shouldn’t rewrite domain. `[S]`/`[B]` for hard DB coupling in core
- **Layering / package structure** — Change placed in correct module; no “utility dumping ground” growth without ownership. `[S]`
- **Coupling** — Temporal, content, control, common, stamp coupling; unwanted fan-out; circular deps. `[B]` for new cycles/hard coupling across ownership
- **Cohesion** — Modules change for one reason; feature cohesion vs coincidental. `[S]`
- **Use-case completeness** — Happy path + failure modes owned by application service, not scattered. `[S]`
- **Frameworks as details** — Framework annotations/types not leaking deep into domain. `[S]`
- **Shared kernels / libraries** — New shared code justified; avoids premature platformization. `[Q]` (Google: belong in library?)
- **Architecture fitness** — Change matches established patterns; if pattern-breaking, PR explains why. `[B]` if silent divergence
- **Blast radius / integration surface** — New cross-service calls, queues, schemas, feature flags documented. `[B]` if undeclared

---

## 3. Code craft (Clean Code / Pragmatic Programmer)
*Informed by: Clean Code; Pragmatic Programmer; Google naming/comments/style; Microsoft readability*

- **Naming** — Intention-revealing; length vs clarity; consistent vocabulary. `[S]`/`[N]`
- **Function size & single purpose** — Small, do one thing; avoid deep nesting. `[S]`
- **Argument lists** — Too many params → parameter object / redesign. `[S]` (MS: >3 is a smell)
- **Duplication (DRY vs coupling)** — Remove harmful dup; don’t abstract premature “almost same”. `[S]`
- **Comments** — Prefer clarity of code; comments explain *why* / constraints / non-obvious; delete lying comments. `[S]` (Google)
- **Dead / commented-out code** — Remove; no inventory of ghosts. `[S]`/`[B]` if masks intent
- **Magic numbers / strings** — Named constants or domain concepts. `[N]`/`[S]`
- **Error handling** — Explicit; don’t swallow; don’t use exceptions for control flow without convention; map to domain errors. `[B]` if silent failure on critical path
- **Null / Optional discipline** — Consistent null policy; avoid null returns when empty collections/Option fit. `[S]`
- **Boolean blindness / flag params** — Prefer explicit types/APIs over `doX(true, false, true)`. `[S]`
- **Side effects visibility** — Pure vs impure clear; surprise mutation flagged. `[S]`/`[B]` if shared mutable state
- **Logging as craft** — Useful, leveled, not noisy; no secrets/PII. `[S]`/`[B]` for PII
- **Idiomatic use of language/stdlib** — Prefer platform facilities over reinvention (Palantir library note). `[S]`
- **Formatting/style** — Defer to linters; humans don’t block on style. `[N]` → automate (Google/MS/Palantir/Orosz)

---

## 4. Design quality
*Informed by: Ousterhout; SOLID (selectively); YAGNI/KISS; Google complexity/over-engineering; Fowler*

- **Complexity budget** — Accidental vs essential; can a reader grasp quickly? (Google/Ousterhout) `[B]` if needless complexity on hot/shared path
- **Deep modules** — Simple interface, nontrivial implementation; avoid shallow class explosion. `[S]`
- **Information hiding** — Internals not leaked; stable abstractions at boundaries. `[S]`/`[B]`
- **Abstraction level consistency** — Mixed high/low level in one function. `[S]`
- **SOLID where useful** — SRP/OCP/LSP/ISP/DIP applied to real pain, not cargo-cult. `[S]`
- **YAGNI / speculative generality** — Google: don’t solve future imaginary problems. `[B]` for heavy over-engineering
- **KISS** — Simplest design that works and stays changeable. `[S]`
- **API of a module** — Hard to misuse; defaults safe (principle of least astonishment). `[S]`/`[B]`
- **Temporal coupling** — Must-call-in-order APIs without enforcement. `[S]`
- **Feature envy / inappropriate intimacy** — Cross-module poking at internals. `[S]`
- **Primitive obsession vs modeling** — Missing domain types. `[S]`
- **Continuation of design debt** — Does PR improve or degrade system design health? (Google standard) `[B]` if net degradation without plan

---

## 5. Change & evolution (CD readiness)
*Informed by: Farley MSE; Accelerate; Google small CLs; Shopify/Meta stacking; trunk-based practice*

- **Incremental deliverability** — Each merge leaves system releasable. `[B]` if intermediate broken states required
- **Feature flags / dark launch** — Incomplete features safely off; flag cleanup plan. `[S]`/`[B]` for risky incomplete behavior on by default
- **Trunk-based implications** — Long-lived branch risk; conflict/staleness. `[S]`
- **Feedback loops** — CI signals meaningful; failing tests not ignored; review not substituting for automation. `[B]` if CI red/ignored
- **Reversibility** — Easy rollback; expand/contract for migrations. `[B]` for irreversible data loss without safeguards
- **Separating refactor from behavior** — Palantir/Google/Shopify: don’t mix. `[S]`/`[B]` if huge mixed PR
- **Evolutionary path** — Parallel run, strangler, dual-write called out when replacing systems. `[Q]`/`[B]`
- **Config vs code change ordering** — Safe order for deploy. `[B]` if wrong order can outage
- **Experiment / kill switch** — For uncertain product/tech bets. `[S]`

---

## 6. Testing strategy
*Informed by: GOOS; xUnit Test Patterns; Farley; Feathers; Google/MS tests guidance*

- **Right altitude (pyramid)** — Unit/integration/e2e balance; avoid ice-cream cone. `[S]`/`[B]` if only brittle e2e for core logic
- **Tests in same PR as code** — Google/MS/Palantir: no “tests next”. `[B]`
- **Behavior vs implementation coupling** — Tests assert outcomes; not overly brittle to structure. `[S]`
- **Edge cases & invariants** — Boundaries, empties, duplicates, clock, locale, concurrency. `[B]` for money/auth/data integrity gaps
- **Characterization tests** — For legacy: lock behavior before change (Feathers). `[S]`/`[B]` if risky legacy untouched
- **Contract / consumer-driven tests** — For APIs/events between services. `[S]`/`[B]` for breaking provider changes
- **Property / generative / fuzz** — Where combinatorial space huge. `[S]`
- **Flaky tests** — New flakiness is a defect; quarantine with ownership. `[B]`
- **Test data & determinism** — No order dependence; control time/random/network. `[B]` if non-deterministic
- **Doubles quality** — Mocks vs fakes; over-mocking smell; verify right interactions. `[S]`
- **Negative / failure-path tests** — Errors, timeouts, partial failure. `[S]`/`[B]` for reliability-critical
- **Security-relevant tests** — Authz deny paths, injection fixtures where applicable. `[S]`
- **Coverage as signal not goal** — Missing critical paths > vanity %. `[Q]`
- **Performance/regression tests** — When change touches known hot path. `[S]`
- **Test readability** — Arrange-Act-Assert / Given-When-Then; tests as docs. `[S]`

---

## 7. Data & consistency
*Informed by: Kleppmann DDIA; Fowler enterprise patterns; Stripe idempotency practices (synthesis + Stripe versioning post)*

- **Schema design** — Types, nullability, constraints, indexes match access patterns. `[B]` if integrity gaps
- **Migrations** — Expand/contract; backward/forward compatible deploys; locking/long migrations risk. `[B]`
- **Transactional boundaries** — What commits together; avoid multi-resource “transactions” without saga/outbox. `[B]`
- **Idempotency** — Writes/handlers safe under retry/at-least-once. `[B]` for payments/fulfillment/side effects
- **Exactly-once illusions** — At-least-once + idempotent consumer preferred; document. `[Q]`
- **Eventual consistency UX** — Stale reads, read-your-writes, conflict resolution. `[S]`/`[B]` if user-visible corruption risk
- **Caching** — TTL, invalidation, stampede, poison cache, consistency with source of truth. `[S]`/`[B]`
- **Data retention / deletion** — GDPR-ish delete paths; soft-delete semantics. `[B]` for privacy requirements
- **Serialization compatibility** — Protobuf/JSON/Avro evolution rules. `[B]`
- **PII storage minimization** — Store only what’s needed; tokenization. `[B]`
- **Backfills** — Rate limits, observability, resume, correctness checks. `[S]`/`[B]`
- **Dual-write hazards** — Two stores updated; failure modes. `[B]` without outbox/CDC plan

---

## 8. Reliability & operability
*Informed by: Release It!; Google SRE; Netflix resilience blogs*

- **Failure modes** — What happens when dependency down/slow/wrong? `[B]` for new critical path deps without plan
- **Timeouts** — Explicit, bounded, consistent with SLOs; no infinite hangs. `[B]`
- **Retries** — Only idempotent; backoff + jitter; retry budget; single retry layer (avoid storms). `[B]` if blind retry on non-idempotent
- **Circuit breakers / bulkheads** — Isolation of failure; fallbacks. `[S]`/`[B]` for high-fanout services
- **Load shedding / backpressure** — Queue bounds; reject vs absorb. `[S]`
- **Graceful degradation** — Partial functionality over total failure. `[S]`
- **Observability** — Logs/metrics/traces for new paths; golden signals (latency, traffic, errors, saturation). `[B]` if new user-critical path is dark
- **SLOs / error budget awareness** — Change risk vs burn. `[Q]` for high-risk
- **Alerting** — Actionable alerts; not pages for symptoms that aren’t actionable. `[S]`
- **Runbooks / ops notes** — Deploy/rollback/feature-flag instructions when behavior changes ops. `[S]`/`[B]` for high-risk
- **Health checks** — Liveness vs readiness correct. `[S]`
- **Resource limits** — Memory/CPU/FD/connection pools; DoS amplification. `[B]` if unbounded
- **Crash-only / restart safety** — Process can die mid-op safely (idempotent + durable state). `[S]`
- **Time & clocks** — Skew, DST, monotonic vs wall clock. `[S]`/`[B]` for scheduling/billing

---

## 9. Security & privacy
*Informed by: OWASP cheat sheet/ASVS/Top 10; Microsoft PII notes; Palantir security section; Secure by Design*

- **Threat modeling lite** — New trust boundaries, assets, attackers (STRIDE-ish). `[Q]`/`[B]` for high-risk features
- **Authentication** — Session/token handling; password storage; MFA touchpoints. `[B]`
- **Authorization** — Server-side; default deny; IDOR; function-level authz; central checks. `[B]`
- **Injection** — SQL/NoSQL/OS/LDAP/template; parameterized queries; path traversal. `[B]`
- **XSS / output encoding** — Context-appropriate encoding. `[B]` for web
- **SSRF / unsafe egress** — User-controlled URLs. `[B]`
- **Deserialization / XXE** — Untrusted data. `[B]`
- **Secrets management** — No hardcoded secrets; rotation; secret scanning. `[B]`
- **Cryptography** — Modern algs; key management; no home-rolled crypto. `[B]`
- **PII / logging** — No PII in logs/metrics/traces/exception messages (MS EUII). `[B]`
- **Privacy controls** — Consent, retention, access, deletion hooks. `[B]` when in scope
- **Security headers / TLS / cookie flags** — When touching HTTP edge. `[S]`/`[B]`
- **Dependency CVEs** — New deps reviewed; pin/lockfiles. `[S]`/`[B]` for known critical
- **Abuse / rate limits** — Expensive endpoints protected. `[S]`/`[B]`
- **Supply chain** — CI permissions, artifact provenance (practice-derived). `[S]`
- **Business logic abuse** — Workflow bypass, race to privilege (OWASP). `[B]`

---

## 10. Performance & scalability
*Informed by: DDIA; Release It!; Google functionality/complexity; MS N+1 note*

- **Hot paths** — Algorithmic complexity on critical request/job paths. `[B]` if obvious O(n²) on large n
- **N+1 queries / chatty I/O** — Batching, joins, data loaders. `[B]`/`[S]` by severity
- **Pagination / unbounded result sets** — Limits enforced. `[B]`
- **Caching strategy** — Correctness + hit rate; stampede. `[S]`
- **Allocation / GC pressure** — Hot loops. `[S]`
- **Concurrency for scale** — Parallelism vs complexity tradeoff. `[Q]`
- **Data volume assumptions** — Documented expected sizes; tested near limits. `[S]`
- **Fan-out amplification** — One request → N downstream. `[B]` if uncontrolled
- **Async offload** — Slow work not on request thread without reason. `[S]`
- **Capacity / cost** — New storage/compute cost called out. `[Q]`/`[S]`

---

## 11. API / contract design
*Informed by: Stripe versioning; API Design Patterns; Google “users of the code”; Palantir backward compat*

- **Backward compatibility** — Additive preferred; no silent renames/type changes. `[B]`
- **Versioning strategy** — Explicit; Stripe-like encapsulation of breaks when needed. `[B]` if break without version story
- **Error shapes** — Stable codes/messages; actionable; no sensitive leak. `[S]`/`[B]`
- **Idempotency keys** — For mutating public APIs. `[B]` for payment-like APIs
- **Pagination/filtering/sorting contracts** — Consistent, documented. `[S]`
- **Pagination tokens vs offset** — Stability under concurrent writes. `[S]`
- **Authn/z at API boundary** — Consistent with codebase (Palantir). `[B]`
- **Payload minimization** — Don’t over-expose fields. `[S]`/`[B]` privacy
- **Event / webhook contracts** — Signature verification, versioning, at-least-once. `[B]`
- **Client SDK impact** — Generated clients / breaking field changes. `[S]`
- **Deprecation policy** — Timeline, dual-run, docs. `[S]`/`[B]`
- **HATEOAS/resource modeling** — Consistency with existing API style. `[S]`
- **Public vs internal API** — Different stability bars. `[Q]`

---

## 12. Concurrency & correctness
*Informed by: Google parallel programming guidance; OWASP race/TOCTOU; Feathers; systems lit*

- **Race conditions** — Shared mutable state; check-then-act. `[B]`
- **Deadlocks / lock ordering** — Documented lock hierarchy. `[B]`
- **Atomicity** — Compare-and-swap / transactions / DB constraints for invariants. `[B]`
- **Memory model / visibility** — Cross-thread publication. `[B]` when applicable
- **Async correctness** — Cancellation, structured concurrency, lost wakeups. `[S]`/`[B]`
- **Idempotent handlers under concurrency** — Unique constraints as safety net. `[B]`
- **Time-of-check/time-of-use** — Filesystem/authz races. `[B]`
- **Ordering guarantees** — Queue/partition assumptions stated. `[Q]`
- **Poison messages / DLQ** — Failure isolation. `[S]`

---

## 13. Developer experience of the change
*Informed by: Pragmatic Programmer; Google docs; Shopify PR map; Palantir maintainability*

- **Local understandability** — Can a teammate grasp without author? `[S]`/`[B]` if impenetrable
- **Docs updates** — README, ADRs, runbooks, API refs when behavior/build/release changes (Google). `[S]`/`[B]`
- **Migration path for callers** — Examples, codemods, deprecation. `[S]`/`[B]` for breaking internal APIs
- **Tooling / DX** — Scripts, Makefile, IDE config, generators updated. `[S]`
- **Discoverability** — New module findable; ownership METADATA/CODEOWNERS. `[S]`
- **Examples & sample usage** — Especially for new libraries/APIs (Google: include usage with new API). `[S]`
- **Cognitive load** — Number of new concepts introduced justified. `[S]`
- **Onboarding impact** — Does this make the system harder for new joiners? (Orosz empathy) `[S]`

---

## 14. Process / PR hygiene
*Informed by: Google small CLs/descriptions; Shopify; Meta stacks; Phabricator why; Pragmatic Engineer; Conventional Comments; MS scope*

- **Size** — Prefer ~100–300 LOC conceptual change; reject/split mega-PRs (Google/Shopify/SWE book). `[B]` to request split when unreviewable
- **Atomicity / one concern** — Feature XOR refactor XOR dep bump (Shopify/Palantir). `[S]`/`[B]`
- **Description quality** — Why, who benefits, what could go wrong, alternatives considered, systems affected (Shopify). `[B]` if empty on non-trivial PR
- **Risk communication** — Rollout plan, monitoring, rollback. `[B]` for high-risk
- **Test plan evidence** — What was run; screenshots for UI (Google/MS). `[S]`/`[B]`
- **Linked issue / product intent** — Traceability. `[S]`
- **Stacking** — Meta/Google stacking for large work. `[S]`
- **Draft/WIP for design feedback** — Shopify early direction. `[S]`
- **Reviewer selection** — Owners + expertise + learners (Shopify/Google OWNERS). `[S]`
- **CI green** — Required checks pass before human deep review (Palantir). `[B]`
- **Commit message quality** — Imperative why (Palantir). `[N]`/`[S]`
- **No drive-by unrelated changes** — MS scope discipline. `[S]`
- **Comment taxonomy** — Conventional Comments labels + blocking decorations. `[S]` process for agent output

---

## 15. Team / org boundaries
*Informed by: Team Topologies; DDD context maps; Orosz cross-timezone deps; Meta ownership; Palantir coupling*

- **Code ownership** — Right OWNERS/reviewers; don’t merge without owning team LGTM. `[B]`
- **Cross-team coupling** — New hard deps creating review/latency bottlenecks (Orosz “better” systemic fix). `[S]`/`[B]`
- **Platform vs product responsibilities** — Leaky abstractions forcing every team to know internals. `[S]`
- **API as team contract** — Changes negotiated; consumer notification. `[B]` for breaking
- **Cognitive load on team** — Too many domains in one service (Team Topologies). `[Q]`
- **Interaction mode** — Collaboration vs X-as-a-Service vs facilitating — implicit mode mismatch. `[Q]`
- **Knowledge bus factor** — Only author understands; needs pairing/docs. `[S]`

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

# What a Principal Engineer prioritizes vs junior over-index

## PE / Staff-style priority stack (review order)
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

## PE “better review” behaviors (Orosz + Google + Palantir)
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
| **Should-fix (suggestion blocking if cheap / issue non-blocking if costly)** | Likely defect or significant maintainability/ops risk; fix if in scope | Prefer fix in PR; allow follow-up issue if PE agrees & risk mitigated | Missing timeout; weak observability on new path; unclear aggregate boundary |
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

**Google standard overlay:** Approve when PR **improves code health** even if imperfect; don’t hold for perfection. PE agent should not recreate perfectionism.

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
