# Checklist — Ops, reliability, performance

Dimensions from taxonomy cats **8**, **10**, plus concurrency leftovers from **12**.

## 8. Reliability & operability

- [ ] **Failure modes** — Dependency down/slow/wrong has a plan. `[B]` for new critical-path deps without plan
- [ ] **Timeouts** — Explicit, bounded, consistent with SLOs. `[B]`
- [ ] **Retries** — Only idempotent; backoff + jitter; single retry layer. `[B]` if blind retry on non-idempotent
- [ ] **Circuit breakers / bulkheads** — Isolation; fallbacks. `[S]`/`[B]` for high-fanout
- [ ] **Load shedding / backpressure** — Queue bounds; reject vs absorb. `[S]`
- [ ] **Graceful degradation** — Partial functionality over total failure. `[S]`
- [ ] **Observability** — Logs/metrics/traces for new paths; golden signals. `[B]` if user-critical path is dark
- [ ] **SLOs / error budget** — Change risk vs burn. `[Q]` for high-risk
- [ ] **Alerting** — Actionable; not symptom spam. `[S]`
- [ ] **Runbooks / ops notes** — Deploy/rollback/flag instructions when ops behavior changes. `[S]`/`[B]` for high-risk
- [ ] **Health checks** — Liveness vs readiness correct. `[S]`
- [ ] **Resource limits** — Memory/CPU/FD/pools; DoS amplification. `[B]` if unbounded
- [ ] **Crash-only / restart safety** — Die mid-op safely. `[S]`
- [ ] **Time & clocks** — Skew, DST, monotonic vs wall. `[S]`/`[B]` for scheduling/billing

## 10. Performance & scalability

- [ ] **Hot paths** — Algorithmic complexity on critical request/job paths. `[B]` if obvious O(n²) on large n
- [ ] **N+1 / chatty I/O** — Batching, joins, loaders. `[B]`/`[S]`
- [ ] **Pagination / unbounded results** — Limits enforced. `[B]`
- [ ] **Caching strategy** — Correctness + stampede. `[S]`
- [ ] **Allocation / GC pressure** — Hot loops. `[S]`
- [ ] **Data volume assumptions** — Expected sizes documented/tested. `[S]`
- [ ] **Fan-out amplification** — One request → N downstream. `[B]` if uncontrolled
- [ ] **Async offload** — Slow work not on request thread without reason. `[S]`
- [ ] **Capacity / cost** — New storage/compute called out. `[Q]`/`[S]`

## Concurrency leftovers (beyond bug-finder races)

- [ ] **Poison messages / DLQ** — Failure isolation for consumers. `[S]`/`[B]`
- [ ] **Async cancellation leftovers** — Orphaned work / inconsistent state after cancel. `[S]`/`[B]`
- [ ] **Ordering guarantees** — Queue/partition assumptions stated. `[Q]`
- [ ] **Concurrent idempotency (ops view)** — Unique constraints / dedupe as safety net for at-least-once consumers. `[B]`

## Clean Code (cat 3) — blocking overlay

- [ ] PII/secrets in logs on new paths → **Blocker**
- [ ] Deep nesting / flag params that hide timeout/retry behavior on hot handlers → **Blocker** if correctness obscured
