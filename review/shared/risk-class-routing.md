# Risk-Class → Pass Routing

`analyze` emits `risk_class`: an array of zero or more of
`domain | auth | data | api | concurrency | ops`.

The orchestrator always runs the foundation passes, then gates the four
Quality Review Task passes on this array.

## Always run

| Pass | Skill / mechanism | Notes |
|---|---|---|
| Change analysis | `review:analyze` | Emits `risk_class` |
| 2-pass bug-finder | Inline Task (opus/sonnet) | Crash/security hunter; expanded concurrency |
| Security scan | `review:security-scan` | Always; deepen when `auth` ∈ risk_class |
| Docs drift | `review:docs-drift` | Always (light DX fold) |

## Risk-gated QR passes

| risk_class value | Run skill | Taxonomy categories |
|---|---|---|
| `domain` | `domain-architecture` | 1 Domain + 2 Architecture + 15 Team/org boundaries |
| `data` | `data-contracts` | 7 Data + 11 API/contracts |
| `api` | `data-contracts` | 7 Data + 11 API/contracts |
| `concurrency` | Expand bug-finder Critical Checks (always on) **and** `ops-reliability` for leftover concurrency beyond races (DLQ/poison, async cancellation leftovers, ordering) | 12 (races in bug-finder) + 8/10 extras |
| `ops` | `ops-reliability` | 8 Reliability + 10 Performance |
| `auth` | Deepen `security-scan` (OWASP authz/IDOR, business-logic abuse, SSRF, PII-in-logs) — no extra QR skill | 9 Security |

## Change / design pass

| Signal | Run skill | Taxonomy categories |
|---|---|---|
| Large PR, mixed refactor+feature, CD/migration/flag work, or design complexity called out in analysis | `change-evolution` | 5 Change/CD + 4 Design quality |

**Rule of thumb:** if `risk_class` is empty, skip the four QR passes (bug-finder + security + docs still run). If unsure whether a class applies, **include** it — false positive pass cost is cheaper than a missed domain/data review.

## Anti-patterns per pass

Every pass carries its own slice at `skills/<pass>/references/anti-patterns.md`,
so a pass can address no slice but its own — the bug-finder's lives under
`skills/review/`, which owns those Tasks. Nothing loads the full taxonomy
(`shared/quality-review-pr-review-taxonomy.md`); it is the provenance for the
slices, not a prompt input.
