## Examples

### Python (pytest)
```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
timeout 600 pytest -v --tb=short --maxfail=10

# Parse
# "23 passed, 2 failed in 45.2s"
```

### JavaScript (jest)
```bash
# Setup
npm ci

# Run
timeout 600 npm test -- --verbose --bail

# Parse
# "Tests: 2 failed, 23 passed, 25 total"
```

### Go
```bash
# Setup (dependencies auto-download)
go mod download

# Run
timeout 600 go test -v -timeout 5m ./...

# Parse
# "PASS" or "FAIL"
```

### Rust (cargo-nextest)
```bash
# Setup
cargo fetch

# Run — unit-only safe subset (full suite needs the compose stack; skip that here)
timeout 600 cargo nextest run -E 'not test(/integration/)' 2>&1 | tail -30
# If the repo has a justfile, `just test` is what CI runs.

# Parse
# "Summary [   1.234s] 206 tests run: 206 passed, 0 skipped"
```

### mac-ui (per-package script)
```bash
# Setup
npm ci

# Run — use the package's own test script; jsdom/vitest are sandbox-safe,
# web-test-runner needs a headless browser (skip if unavailable).
timeout 600 npm -w <package> test 2>&1 | tail -30
```

### Java (Maven)
```bash
# Setup
mvn test-compile

# Run
timeout 600 mvn test -Dmaven.test.failure.ignore=false

# Parse
# "Tests run: 25, Failures: 2"
```
