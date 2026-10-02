# Anti-patterns — Bug-finder (crash / security hunter)

Read **only** this file for the orchestrator's 3-pass bug-finder. Do not load other anti-pattern slices.

## Crash / lifecycle

- Null deref after cleanup / error path / cross-thread nulling
- Resource opened but not closed on all paths (including exceptions)
- Missing return after cleanup; early exit skipping cleanup
- Unreachable code hiding broken control flow

## Security sinks

- External input reaching SQL / HTML / shell / file path / log sinks without sanitization
- Hardcoded secrets
- Sensitive data in logs
- Missing auth checks on new surfaces
- Client-trusted authorization / prices / roles

## Concurrency (expanded)

- Shared mutable state without synchronization; check-then-act races
- Deadlocks / lock-ordering violations
- TOCTOU (filesystem, authz, existence checks)
- Async cancellation / lost wakeups / unstructured concurrency leaving inconsistent state
- Concurrent idempotency gaps (handler not safe under parallel retries; missing unique constraints)
- Poison messages / missing DLQ isolation on consumers

## Architectural consistency (crash-adjacent)

- Mixing two APIs for one purpose in a way that drops cleanup/auth
- Wrappers/utilities removed without replacing safety guarantees

## Clean Code (blocking when correctness-adjacent)

- Empty catch / catch-all Exception on paths that can crash or corrupt
- Shared mutable globals enabling races
