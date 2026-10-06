# Checklist — Data & API contracts

Dimensions from taxonomy categories **7 Data & consistency** and **11 API / contract design**.

## 7. Data & consistency

- [ ] **Schema design** — Types, nullability, constraints, indexes match access patterns. `issue (blocking)` if integrity gaps
- [ ] **Migrations** — Expand/contract; backward/forward compatible deploys; locking risk. `issue (blocking)`
- [ ] **Transactional boundaries** — What commits together; avoid multi-resource tx without saga/outbox. `issue (blocking)`
- [ ] **Idempotency** — Writes/handlers safe under retry/at-least-once. `issue (blocking)` for payments/fulfillment/side effects
- [ ] **Exactly-once illusions** — Prefer at-least-once + idempotent consumer; document. `issue (blocking)` when code assumes exactly-once; `question` otherwise
- [ ] **Eventual consistency UX** — Stale reads, conflict resolution. `issue (blocking)` if user-visible corruption risk
- [ ] **Caching** — TTL, invalidation, stampede, poison cache. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Data retention / deletion** — Delete paths; soft-delete semantics. `issue (blocking)` for privacy requirements
- [ ] **Serialization compatibility** — Protobuf/JSON/Avro evolution rules. `issue (blocking)`
- [ ] **PII storage minimization** — Store only what's needed. `issue (blocking)`
- [ ] **Backfills** — Rate limits, observability, resume, correctness checks. `issue (blocking)`
- [ ] **Dual-write hazards** — Two stores updated; failure modes. `issue (blocking)` without outbox/CDC plan

## 11. API / contract design

- [ ] **Backward compatibility** — Additive preferred; no silent renames/type changes. `issue (blocking)`
- [ ] **Versioning strategy** — Explicit; encapsulate breaks. `issue (blocking)` if break without version story
- [ ] **Error shapes** — Stable codes; no sensitive leak. `issue (blocking)` on public APIs
- [ ] **Idempotency keys** — For mutating public APIs. `issue (blocking)` for payment-like APIs
- [ ] **Pagination/filtering/sorting** — Consistent, documented. `issue (blocking)` for new public endpoints — consistency is part of the contract
- [ ] **Pagination tokens vs offset** — Stability under concurrent writes. `issue (blocking)` when concurrent writes are possible — offset silently skips rows
- [ ] **Authn/z at API boundary** — Consistent with codebase. `issue (blocking)`
- [ ] **Payload minimization** — Don't over-expose fields. `issue (blocking)`
- [ ] **Event / webhook contracts** — Signature verification, versioning, at-least-once. `issue (blocking)`
- [ ] **Client SDK impact** — Generated clients / breaking field changes. `issue (blocking)` for breaking field changes
- [ ] **Deprecation policy** — Timeline, dual-run, docs. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Public vs internal API** — Different stability bars. `question`

## Clean Code (category 3 Code craft) — blocking overlay

- [ ] ORM entities leaked as API DTOs → **Blocker** · Extract Class (separate the DTO)
- [ ] Swallowed errors on write/migration paths → **Blocker**
- [ ] Magic version/schema strings on shared contracts → **Blocker** · Replace Magic Literal
