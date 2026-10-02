# Checklist — Data & API contracts

Dimensions from taxonomy cats **7** and **11**.

## 7. Data & consistency

- [ ] **Schema design** — Types, nullability, constraints, indexes match access patterns. `[B]` if integrity gaps
- [ ] **Migrations** — Expand/contract; backward/forward compatible deploys; locking risk. `[B]`
- [ ] **Transactional boundaries** — What commits together; avoid multi-resource tx without saga/outbox. `[B]`
- [ ] **Idempotency** — Writes/handlers safe under retry/at-least-once. `[B]` for payments/fulfillment/side effects
- [ ] **Exactly-once illusions** — Prefer at-least-once + idempotent consumer; document. `[Q]`
- [ ] **Eventual consistency UX** — Stale reads, conflict resolution. `[B]` if user-visible corruption risk
- [ ] **Caching** — TTL, invalidation, stampede, poison cache. `[S]`/`[B]`
- [ ] **Data retention / deletion** — Delete paths; soft-delete semantics. `[B]` for privacy requirements
- [ ] **Serialization compatibility** — Protobuf/JSON/Avro evolution rules. `[B]`
- [ ] **PII storage minimization** — Store only what's needed. `[B]`
- [ ] **Backfills** — Rate limits, observability, resume, correctness checks. `[S]`/`[B]`
- [ ] **Dual-write hazards** — Two stores updated; failure modes. `[B]` without outbox/CDC plan

## 11. API / contract design

- [ ] **Backward compatibility** — Additive preferred; no silent renames/type changes. `[B]`
- [ ] **Versioning strategy** — Explicit; encapsulate breaks. `[B]` if break without version story
- [ ] **Error shapes** — Stable codes; no sensitive leak. `[S]`/`[B]`
- [ ] **Idempotency keys** — For mutating public APIs. `[B]` for payment-like APIs
- [ ] **Pagination/filtering/sorting** — Consistent, documented. `[S]`
- [ ] **Pagination tokens vs offset** — Stability under concurrent writes. `[S]`
- [ ] **Authn/z at API boundary** — Consistent with codebase. `[B]`
- [ ] **Payload minimization** — Don't over-expose fields. `[S]`/`[B]` privacy
- [ ] **Event / webhook contracts** — Signature verification, versioning, at-least-once. `[B]`
- [ ] **Client SDK impact** — Generated clients / breaking field changes. `[S]`
- [ ] **Deprecation policy** — Timeline, dual-run, docs. `[S]`/`[B]`
- [ ] **Public vs internal API** — Different stability bars. `[Q]`

## Clean Code (cat 3) — blocking overlay

- [ ] ORM entities leaked as API DTOs → **Blocker**
- [ ] Swallowed errors on write/migration paths → **Blocker**
- [ ] Magic version/schema strings on shared contracts without names → Suggestion (or Blocker if they enable silent break)
