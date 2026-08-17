# Rust test-gap analysis

The default file-convention mapping (`src/x.py` → `tests/test_x.py`) is WRONG
for Rust: unit tests live in-file in a `#[cfg(test)] mod tests` block in the
same `.rs`, and `#[tokio::test]` is common for async. Integration tests live in
`tests/` at the crate root. Adapt as follows.

## Map changed code to tests

For each changed item, search the same file's `mod tests` (and crate `tests/`)
for a `#[test]`/`#[tokio::test]` that exercises it:

```bash
# Does the changed fn / variant have a test referencing it?
grep -rn "fn <name>\|<Enum>::<Variant>\|<symbol>" --include='*.rs' \
  <crate>/src <crate>/tests | grep -A0 -i test
```

Untested if no test names the symbol or its behavior.

## Prefer real coverage over the 70% heuristic

If `cargo-llvm-cov` is available and the suite is runnable (see the analyze
safety gate — DB/Kafka may be required), get real per-file coverage instead of
guessing:

```bash
cargo llvm-cov nextest --workspace --json --summary-only 2>/dev/null
# or the repo's gate, which encodes the threshold CI enforces:
just coverage 2>&1 | tail -20
```

Report the repo's own `--fail-under-lines` threshold as the target (this repo
gates the workspace TOTAL at 90%), not the generic 80%.

## High-value Rust gaps to name explicitly

These are the ones a coverage percentage hides but reviews keep surfacing:

- **Unreachable/untested error arms.** A `match` arm or `ZoomError` variant that
  no test (and no fake) can produce — e.g. an `Auth | RateLimited` arm that the
  fake never returns. Flag the specific arm, not just the file %.
- **Untested `from_env`/config branches.** Each env-parse branch (unset, blank,
  valid, invalid) is a distinct path; name the missing ones.
- **New `pub fn` / trait impl with no `#[test]`.**
- **A scenario/knob added in code but not selectable** (so the test that would
  exercise it can't).

Tie each gap to the exact symbol + line, and (when coverage ran) the measured
percentage for that file.
