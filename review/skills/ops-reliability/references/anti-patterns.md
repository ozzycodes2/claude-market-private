# Anti-patterns — Ops, reliability, performance

## Reliability / operability

- Missing timeouts (infinite hangs)
- Blind retries on non-idempotent operations; retry storms (multiple layers)
- Cascading failure without circuit breakers / bulkheads / isolation
- New user-critical path with no logs/metrics/traces (dark path)
- Unbounded queues/pools/result sets (resource exhaustion / DoS amplification)
- Silent swallowing of errors on critical paths
- Wrong liveness vs readiness semantics
- Irreversible deploy/config order that can outage

## Performance / scalability

- Obvious O(n²) or unbounded work on hot request/job paths
- N+1 / chatty I/O without batching
- Uncontrolled fan-out (one request → N downstream)
- Unbounded pagination / missing limits
- Cache stampede / incorrect invalidation on hot keys

## Concurrency leftovers (beyond race-focused bug-finder)

- Poison messages ignored; no DLQ / failure isolation
- Async cancellation / structured-concurrency gaps leaving work orphaned
- Ordering/partition assumptions undocumented
- Concurrent idempotency without unique constraints as safety net (when ops-facing)

## Clean Code (blocking)

- Logging that is noisy enough to hide incidents, or that includes secrets/PII
- Deep nesting / boolean flagparams on hot-path handlers that obscure failure modes
