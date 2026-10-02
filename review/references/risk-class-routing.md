# Risk-Class → Pass Routing

`analyze` emits `risk_class`: an array of zero or more of
`domain | auth | data | api | concurrency | ops`.

The orchestrator always runs the foundation passes, then gates the four
principal-engineer Task passes on this array (plus light always-on hygiene).

## Always run

| Pass | Skill / mechanism | Notes |
|---|---|---|
| Change analysis | `review:analyze` | Emits `risk_class` + PR hygiene preflight |
| 3-pass bug-finder | Inline Task (opus/sonnet/haiku) | Crash/security hunter; expanded concurrency |
| Security scan | `review:security-scan` | Always; deepen when `auth` ∈ risk_class |
| Docs drift | `review:docs-drift` | Always (light DX fold) |
| Codegen | `review:codegen` | Always |

## Risk-gated PE passes

| risk_class value | Run skill | Taxonomy cats |
|---|---|---|
| `domain` | `domain-architecture` | 1 Domain + 2 Architecture + 15 Team/org boundaries |
| `data` | `data-contracts` | 7 Data + 11 API/contracts |
| `api` | `data-contracts` | 7 Data + 11 API/contracts |
| `concurrency` | Expand bug-finder Critical Checks (always on) **and** `ops-reliability` for leftover concurrency beyond races (DLQ/poison, async cancellation leftovers, ordering) | 12 (races in bug-finder) + 8/10 extras |
| `ops` | `ops-reliability` | 8 Reliability + 10 Performance |
| `auth` | Deepen `security-scan` (OWASP authz/IDOR, business-logic abuse, SSRF, PII-in-logs) — no extra PE skill | 9 Security |

## Change / design pass

| Signal | Run skill | Taxonomy cats |
|---|---|---|
| Large PR, mixed refactor+feature, CD/migration/flag work, or design complexity called out in analysis | `change-evolution` | 5 Change/CD + 4 Design quality |
| Hygiene preflight flags size/one-concern/description gaps | Prefer running `change-evolution` even if risk_class is empty | — |

**Rule of thumb:** if `risk_class` is empty and hygiene is clean, skip the four PE passes (bug-finder + security + docs still run). If unsure whether a class applies, **include** it — false positive pass cost is cheaper than a missed domain/data review.

## Anti-patterns file per pass

Each pass reads **only** its matching slice under `review/references/anti-patterns/`:

| Pass | Anti-patterns file |
|---|---|
| `domain-architecture` | `anti-patterns/domain-architecture.md` |
| `data-contracts` | `anti-patterns/data-contracts.md` |
| `ops-reliability` | `anti-patterns/ops-reliability.md` |
| `change-evolution` | `anti-patterns/change-evolution.md` |
| bug-finder (3-pass) | `anti-patterns/bug-finder.md` |
| `security-scan` | `anti-patterns/security-scan.md` |

Do **not** load the full taxonomy or other passes' anti-pattern files into a single prompt.
