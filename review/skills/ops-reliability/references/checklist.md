# Checklist — Ops, reliability, performance

Dimensions from taxonomy categories **8 Reliability & operability**, **10 Performance & scalability**, plus concurrency leftovers from **12 Concurrency & correctness**.

## 8. Reliability & operability

- [ ] **Failure modes** — Dependency down/slow/wrong has a plan. `issue (blocking)` for new critical-path deps without plan
- [ ] **Timeouts** — Explicit, bounded, consistent with SLOs. `issue (blocking)`
- [ ] **Retries** — Only idempotent; backoff + jitter; single retry layer. `issue (blocking)` if blind retry on non-idempotent
- [ ] **Circuit breakers / bulkheads** — Isolation; fallbacks. `suggestion (non-blocking)`/`issue (blocking)` for high-fanout
- [ ] **Load shedding / backpressure** — Queue bounds; reject vs absorb. `suggestion (non-blocking)`
- [ ] **Graceful degradation** — Partial functionality over total failure. `suggestion (non-blocking)`
- [ ] **Observability** — Logs/metrics/traces for new paths; golden signals. `issue (blocking)` if user-critical path is dark
- [ ] **SLOs / error budget** — Change risk vs burn. `question` for high-risk
- [ ] **Alerting** — Actionable; not symptom spam. `suggestion (non-blocking)`
- [ ] **Runbooks / ops notes** — Deploy/rollback/flag instructions. `issue (blocking)` whenever ops behavior changes
- [ ] **Health checks** — Liveness vs readiness correct. `issue (blocking)` — wrong semantics causes restart loops
- [ ] **Resource limits** — Memory/CPU/FD/pools; DoS amplification. `issue (blocking)` if unbounded
- [ ] **Crash-only / restart safety** — Die mid-op safely. `issue (blocking)`
- [ ] **Time & clocks** — Skew, DST, monotonic vs wall. `issue (blocking)` — clock bugs are silent and expensive

## 10. Performance & scalability

- [ ] **Hot paths** — Algorithmic complexity on critical request/job paths. `issue (blocking)` if obvious O(n²) on large n
- [ ] **N+1 / chatty I/O** — Batching, joins, loaders. `issue (blocking)`/`suggestion (non-blocking)`
- [ ] **Pagination / unbounded results** — Limits enforced. `issue (blocking)`
- [ ] **Caching strategy** — Correctness + stampede. `issue (blocking)` on shared paths (invalidation correctness)
- [ ] **Allocation / GC pressure** — Hot loops. `suggestion (non-blocking)`
- [ ] **Data volume assumptions** — Expected sizes documented/tested. `suggestion (non-blocking)`
- [ ] **Fan-out amplification** — One request → N downstream. `issue (blocking)` if uncontrolled
- [ ] **Async offload** — Slow work not on request thread without reason. `issue (blocking)` when slow work sits on a request path
- [ ] **Capacity / cost** — New storage/compute called out. `question`/`suggestion (non-blocking)`

## Concurrency leftovers (beyond bug-finder races)

- [ ] **Poison messages / DLQ** — Failure isolation for consumers. `suggestion (non-blocking)`/`issue (blocking)`
- [ ] **Async cancellation leftovers** — Orphaned work / inconsistent state after cancel. `issue (blocking)`
- [ ] **Ordering guarantees** — Queue/partition assumptions stated. `issue (blocking)` when code depends on order without stating it; `question` otherwise
- [ ] **Concurrent idempotency (ops view)** — Unique constraints / dedupe as safety net for at-least-once consumers. `issue (blocking)`

## Clean Code (category 3 Code craft) — blocking overlay

- [ ] PII/secrets in logs on new paths → **Blocker**
- [ ] Deep nesting that hides timeout/retry behavior → **Blocker** · Replace Nested Conditional with Guard Clauses
- [ ] Boolean flag params on handlers → **Blocker** · Remove Flag Argument
- [ ] Logging noisy enough to hide an incident → **high**
