# Anti-patterns — Data & API contracts

## Data & consistency

- Dual writes without outbox/CDC plan
- Non-idempotent handlers under at-least-once delivery
- Migrations that lock prod or skip expand/contract
- Integrity gaps: missing constraints/nullability/indexes for the access pattern
- Unbounded queries; poison caches without invalidation story
- Serialization breaks (JSON/Protobuf/Avro) without compatibility rules
- PII stored beyond need; delete/retention paths missing when required
- Multi-resource “transactions” without saga/outbox

## API / contracts

- Silent renames / type changes / field removals without version story
- Mutating public APIs without idempotency keys (payment-like)
- Breaking event/webhook contracts without signature/versioning/at-least-once story
- Over-exposing payload fields (privacy)
- Authn/z inconsistent at API boundary
- Deprecation without dual-run timeline or caller migration docs
- Error shapes that leak sensitive internals

## Clean Code (blocking when on shared/hot paths)

- Leaking ORM entities as public API DTOs
- Catch-all Exception swallowing on write/migration paths
- Magic strings for schema/version identifiers on shared contracts
