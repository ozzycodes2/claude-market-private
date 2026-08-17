# Rust security & correctness scan

semgrep `--config=auto` has thin Rust coverage and there is no bandit/gosec
equivalent, so **cargo tooling is the scanner** for Rust. Run what's available;
report what isn't installed rather than silently skipping.

## Supply-chain tools (run when present)

```bash
command -v cargo-audit  >/dev/null && cargo audit --json            # RUSTSEC CVEs
command -v cargo-deny   >/dev/null && cargo deny --format json check advisories bans licenses sources
command -v cargo-machete>/dev/null && cargo machete                 # unused deps
# clippy is the highest-signal Rust linter; run it if the toolchain is present.
cargo clippy --workspace --all-targets -- -D warnings 2>&1 | tail -40
# Prefer the repo's own gate if a justfile defines it (same as CI):
command -v just >/dev/null && just clippy 2>&1 | tail -40
```

Map results: RUSTSEC advisory → dependency finding (severity from CVSS);
`cargo deny` ban/license violation → dependency finding; clippy `-D warnings`
failures in changed files → code findings.

## Correctness / PHI pattern catalog (grep changed `.rs`, non-test code)

These are the classes that recur across review rounds on this codebase. For
each hit, trace it (don't just match) and confirm it's in non-test code
(`#[cfg(test)]` modules are exempt for `unwrap`/`expect`).

| Pattern | Grep seed | Why it's a finding |
|---|---|---|
| Secret/PHI behind `#[derive(Debug)]` | `derive(` … `Debug` on a struct holding a token/secret/`callee`/`address`/`email`/`login`/phone | `{:?}` leaks it into logs; use a redacting manual/`debug_redacted!` impl |
| Sensitive value logged | `info!`/`warn!`/`debug!`/`println!`/`dbg!` near a field that is PHI/secret | zero-PHI logging rule; redact or drop |
| Blank env → `Some("")` | `env::var(` … `).ok()` without a trim/emptiness guard | present-but-empty var becomes `Some("")`, silently mis-configuring live paths |
| Silent enum fallback | `==` string compare on an env value with an `else`/default arm | an unrecognized value silently means the safe default (e.g. "no calls placed" while API reports success) — parse to an enum that errors |
| HTTP client without timeout | `reqwest::Client::new()` / `ClientBuilder` with no `.timeout(`/`.connect_timeout(` | a hung request leaves the operation with no terminal state |
| Timeout bypassed | `#[derive(… Default)]` or `unwrap_or_default()` on a client wrapper whose `new()` sets timeouts | the default path skips the timeouts |
| `unwrap`/`expect`/`panic!`/`unsafe` in non-test | `.unwrap()` `.expect(` `panic!` `unsafe ` | crash / UB risk; require justification |
| Unhandled error arm collapse | a `match` on an error that maps distinct failures to one business outcome | schema-drift/auth failures masquerading as "operator unavailable" etc. |

## Severity guidance

- **Critical:** secret/PHI actually reachable in a log/Debug path; a live-mode
  misconfiguration that dials/acts on wrong input.
- **High:** RUSTSEC CVE (CVSS ≥ 7) in a used dep; missing HTTP timeout on the
  outbound path; `unsafe` without invariants.
- **Medium/Low:** unused deps, lint-level clippy, non-test `unwrap` in clearly
  infallible spots.

Report Rust findings as their own cluster so they're not lost among generic
semgrep output.
