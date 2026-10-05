# Anti-patterns — Domain / Architecture / Team boundaries

## Domain

- Accidental synonyms inventing conflicting public terms (`User` vs `Account` vs `Customer` for the same concept)
- Cross-context model merge / leaking foreign concepts into the core model
- Invariants enforced “eventually” across aggregates without explicit saga/outbox design
- Domain logic buried in controllers, repos, or UI
- Foreign/legacy DTOs becoming internal source of truth (missing anti-corruption layer)
- Domain events that invent alternate truths in consumers or dump whole aggregates as payload

## Architecture

- Inner layers depending on outer (UI/DB/framework leaking inward)
- Hard DB/framework types in domain core
- New circular dependencies or hard coupling across ownership boundaries
- Silent architecture-pattern divergence without PR explanation
- Undeclared blast radius: new cross-service calls, queues, schemas, flags with no callout
- Premature shared-kernel / platform library without justification

## Team / org boundaries

- Merging without owning team / CODEOWNERS LGTM on foreign code
- New hard cross-team deps that create review/latency bottlenecks without negotiation
- Breaking API-as-team-contract without consumer notification
- Platform leak forcing every product team to know internals
- Bus-factor: only the author understands the change; no docs/pairing path

## Clean Code (blocking when on shared/hot paths)

- Silent catch / swallowed errors on domain-critical paths
- Shared mutable global/singleton state crossing module boundaries
- Layering violations (SQL in controllers, HTTP in domain)
- God class / god service growth without ownership
