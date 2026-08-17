---
name: run-tests
description: Safely execute tests in isolated environment with timeout and resource limits. Use when reviewing a PR and you need to actually run its tests in a sandboxed, resource-limited environment.
allowed-tools: Bash Read
---

# Test Runner

Executes tests safely in an isolated environment with strict timeout and resource limits. Only runs tests deemed safe by the analyze skill.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Directory for output files. Defaults to a private `mktemp -d` directory if not provided.
- **Analysis JSON**: From `analyze` at `$OUTPUT_DIR/pr-analysis-<number>.json`

## Outputs

Writes test results to `$OUTPUT_DIR/test-results-<PR_NUMBER>.json` with structure:
```json
{
  "pr_number": 123,
  "execution_timestamp": "2025-02-07T10:30:00Z",
  "status": "completed|failed|timeout|skipped",
  "safety_check": {
    "passed": true,
    "can_run": true,
    "reasons": ["Uses standard test framework", "No external dependencies"]
  },
  "execution": {
    "command": "pytest",
    "exit_code": 0,
    "duration_seconds": 45,
    "timeout_seconds": 600,
    "timed_out": false
  },
  "results": {
    "total": 23,
    "passed": 23,
    "failed": 0,
    "skipped": 0,
    "errors": 0
  },
  "failures": [],
  "output": "<captured stdout/stderr>",
  "summary": "All 23 tests passed in 45 seconds"
}
```

## Prerequisites

Load PR analysis:
```bash
cat "$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json"
```

**Safety check:**
```json
if (test_setup.can_run_safely !== true) {
  SKIP: "Tests cannot be run safely (requires manual execution)"
}
```

## Step 0: Parse Arguments

Extract PR URL and output directory from arguments:

```bash
PR_URL="$1"
# Default to a private per-run temp dir when run standalone (no OUTPUT_DIR passed)
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"

# Extract PR number for filename
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')

echo "Output directory: $OUTPUT_DIR" >&2
echo "PR number: $PR_NUMBER" >&2

# Load PR analysis
ANALYSIS_FILE="$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
if [ ! -f "$ANALYSIS_FILE" ]; then
  echo "ERROR: Analysis file not found: $ANALYSIS_FILE" >&2
  exit 1
fi
```

## Step 1: Safety Validation

### 1.1 Verify Safety Flags

From analysis JSON, check:
- `test_setup.can_run_safely` must be `true`
- `test_setup.framework` must be recognized (pytest, jest, go test, etc.)
- `test_setup.test_command` must be non-destructive

### 1.2 Additional Safety Checks

**Forbidden patterns in test commands:**
```bash
# Check test command for dangerous patterns
DANGEROUS_PATTERNS=(
  "rm -rf"
  "dd if="
  "mkfs"
  "> /dev"
  "curl.*prod\|production"
  "ssh"
  "docker run.*--privileged"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$TEST_COMMAND" | grep -qE "$pattern"; then
    echo "UNSAFE: Test command contains dangerous pattern: $pattern"
    exit 1
  fi
done
```

**Blocked operations:**
- Filesystem writes outside `/tmp` or test workspace
- Network requests to production domains
- System modifications (users, permissions, services)
- Resource-intensive operations (fork bombs, infinite loops)

### 1.3 Resource Limits

Set strict limits. `ulimit` takes numeric values (KB for `-v`/`-f`, seconds for `-t`), so use integers — string values like `"2g"` evaluate to `0` in arithmetic and silently disable the limit.

```bash
# Maximum wall-clock execution time: 10 minutes (enforced by `timeout`)
TIMEOUT=600

# Maximum virtual memory: 2GB, expressed in KB for `ulimit -v`
MEM_KB=2097152   # 2 * 1024 * 1024

# Maximum single-file size: 1GB, expressed in KB for `ulimit -f`
# NOTE: `ulimit -f` limits the size of any single file the process writes,
# NOT total disk usage. There is no portable per-process total-disk limit.
FILE_KB=1048576  # 1 * 1024 * 1024
```

## Step 2: Prepare Test Environment

### 2.1 Create Isolated Workspace

```bash
# Create temporary directory
WORKSPACE=$(mktemp -d -t pr-test-XXXXXX)
cd "$WORKSPACE"

echo "Test workspace: $WORKSPACE"
```

### 2.2 Checkout PR Code

```bash
# Extract repo info from PR URL
REPO_URL=$(echo "$PR_URL" | sed -E 's|(https://[^/]+/[^/]+/[^/]+)/pull/.*|\1|')
PR_NUMBER=$(echo "$PR_URL" | sed -E 's|.*/pull/([0-9]+)|\1|')

# Clone repository
git clone "$REPO_URL.git" repo
cd repo

# Fetch PR
gh pr checkout "$PR_NUMBER"
```

**Error handling:**
```bash
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to checkout PR"
  exit 1
fi
```

### 2.3 Install Dependencies (Safely)

**Python:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies with timeout
timeout 300 pip install -r requirements.txt

if [ $? -eq 124 ]; then
  echo "ERROR: Dependency installation timed out (5min limit)"
  exit 1
fi
```

**JavaScript:**
```bash
# Install with timeout
timeout 300 npm ci  # Use ci for reproducible installs

if [ $? -eq 124 ]; then
  echo "ERROR: npm install timed out (5min limit)"
  exit 1
fi
```

**Go:**
```bash
# Go modules (usually fast)
go mod download
```

**Java:**
```bash
# Maven
timeout 300 mvn test-compile

# Gradle
timeout 300 ./gradlew testClasses
```

## Step 3: Execute Tests with Safety Constraints

### 3.1 Build Test Command

From analysis JSON:
```bash
TEST_COMMAND=$(jq -r '.test_setup.test_command' "$ANALYSIS_FILE")

# Add any necessary flags
# Python: pytest -v --tb=short
# JavaScript: npm test -- --verbose
# Go: go test -v ./...
# Java: mvn test
# Rust: cargo nextest run   (or `just test`); run the unit-only safe subset the
#       analyze step recorded when the full suite needs live infra.
# mac-ui: the package.json `test` script (per-package), NOT a guessed command.
```

**Rust safety gate:** only run when `analyze` marked the suite safe. The full
workspace suite that gates on `PGURL`/`KAFKA_BOOTSTRAP_SERVERS`/`RUN_KAFKA_TESTS`
or a `just compose-up` stack is NOT safe here — run the recorded unit-only
subset (e.g. `cargo nextest run -E 'not test(/integration/)'`) or skip and tell
the reviewer coverage/integration must run locally with the compose stack up.

**mac-ui safety gate:** web-test-runner needs a headless browser that a sandbox
may lack — if `analyze` marked it unsafe, skip and report, don't force it.

### 3.2 Run Tests with Timeout and Limits

**Using timeout + resource limits:**

```bash
# Set resource limits (numeric values only). Wall-clock time is enforced by
# `timeout` below, so we do NOT set `ulimit -t` (a CPU-seconds limit would race
# with, and be redundant to, the wall-clock timeout).
ulimit -v "$MEM_KB"   # Virtual memory limit (KB) — best-effort, OS-dependent
ulimit -f "$FILE_KB"  # Single-file size limit (KB), NOT total disk

# Run tests with wall-clock timeout, capturing output to the session dir
timeout "$TIMEOUT" bash -c "$TEST_COMMAND" > "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" 2>&1
EXIT_CODE=$?

# Check timeout
if [ $EXIT_CODE -eq 124 ]; then
  echo "⚠️ Tests timed out after ${TIMEOUT} seconds"
  TIMED_OUT=true
else
  TIMED_OUT=false
fi
```

**Capture timing:**
```bash
START_TIME=$(date +%s)
# ... run tests ...
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
```

### 3.3 Network Isolation (Optional - if supported)

**Linux (using network namespaces):**
```bash
# Run tests without network access
unshare --net bash -c "$TEST_COMMAND"
```

**macOS (using pfctl - requires sudo, skip if not available):**
```bash
# Network isolation harder on macOS, skip for now
echo "Network isolation not available on macOS"
```

## Step 4: Parse Test Results

### 4.1 Detect Result Format

**Pytest (Python):**
```bash
# Look for pytest output
grep "passed\|failed\|skipped\|error" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log"

# Parse: "23 passed, 2 failed, 1 skipped in 45.2s"
PASSED=$(grep -oE "[0-9]+ passed" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "[0-9]+")
FAILED=$(grep -oE "[0-9]+ failed" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "[0-9]+")
SKIPPED=$(grep -oE "[0-9]+ skipped" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "[0-9]+")
```

**Jest (JavaScript):**
```bash
# Look for Jest summary
# "Tests: 2 failed, 23 passed, 25 total"
FAILED=$(grep "Tests:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+")
PASSED=$(grep "Tests:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+")
```

**Go:**
```bash
# Look for "PASS" or "FAIL"
if grep -q "^FAIL" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log"; then
  STATUS="failed"
else
  STATUS="passed"
fi

# Count tests
TOTAL=$(grep -c "^--- PASS:\|^--- FAIL:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log")
```

**JUnit (Java):**
```bash
# Parse Maven/Gradle output
# "Tests run: 25, Failures: 2, Errors: 0, Skipped: 1"
TOTAL=$(grep "Tests run:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "Tests run: [0-9]+" | grep -oE "[0-9]+")
FAILED=$(grep "Failures:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | grep -oE "Failures: [0-9]+" | grep -oE "[0-9]+")
```

### 4.2 Extract Failure Details

If tests failed, extract failure information:

```bash
# Find failure details
grep -A 10 "FAILED\|FAIL:\|AssertionError\|Error:" "$OUTPUT_DIR/test-output-${PR_NUMBER}.log" | head -100
```

**Structure failures:**
```json
{
  "test_name": "test_validate_token_expired",
  "file": "tests/test_auth.py",
  "line": 67,
  "error": "AssertionError: Expected False, got True",
  "traceback": "<full traceback>"
}
```

## Step 5: Assess Test Results

### 5.1 Determine Overall Status

```
IF (timed_out):
  STATUS = "timeout"
  SUMMARY = "Tests exceeded ${TIMEOUT}s limit"

ELIF (exit_code != 0 AND failed > 0):
  STATUS = "failed"
  SUMMARY = "${failed} of ${total} tests failed"

ELIF (exit_code != 0 AND failed == 0):
  STATUS = "error"
  SUMMARY = "Test execution error (setup issue?)"

ELIF (passed > 0):
  STATUS = "passed"
  SUMMARY = "All ${passed} tests passed in ${duration}s"

ELSE:
  STATUS = "unknown"
  SUMMARY = "Could not determine test results"
```

### 5.2 Analyze Failure Patterns

If tests failed, categorize:

**Flaky tests** (if re-run shows different results):
- Random failures
- Timing-dependent
- Non-deterministic

**Real failures** (consistent):
- Assertion errors
- Exceptions
- Logical errors

**Setup failures:**
- Import errors
- Missing dependencies
- Configuration issues

## Step 6: Generate Test Results JSON

Build the JSON with `jq -n` so PR-derived values (the test command and captured output) are safely escaped — pass numbers/arrays/objects with `--argjson` and plain strings with `--arg`. Never interpolate untrusted text directly into a heredoc. The `*_JSON` variables below must already be valid JSON (build them with `jq`).

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg execution_timestamp "$(date -Iseconds)" \
  --arg status "$STATUS" \
  --argjson safety_reasons "$SAFETY_REASONS_JSON" \
  --arg command "$TEST_COMMAND" \
  --argjson exit_code "$EXIT_CODE" \
  --argjson duration_seconds "$DURATION" \
  --argjson timeout_seconds "$TIMEOUT" \
  --argjson timed_out "$TIMED_OUT" \
  --argjson total "$TOTAL" \
  --argjson passed "$PASSED" \
  --argjson failed "$FAILED" \
  --argjson skipped "$SKIPPED" \
  --argjson errors "$ERRORS" \
  --argjson failures "$FAILURES_JSON" \
  --arg output "$TEST_OUTPUT" \
  --arg summary "$SUMMARY" \
  '{
    pr_number: $pr_number,
    execution_timestamp: $execution_timestamp,
    status: $status,
    safety_check: {
      passed: true,
      can_run: true,
      reasons: $safety_reasons
    },
    execution: {
      command: $command,
      exit_code: $exit_code,
      duration_seconds: $duration_seconds,
      timeout_seconds: $timeout_seconds,
      timed_out: $timed_out
    },
    results: {
      total: $total,
      passed: $passed,
      failed: $failed,
      skipped: $skipped,
      errors: $errors
    },
    failures: $failures,
    output: $output,
    summary: $summary
  }' > "$OUTPUT_DIR"/test-results-${PR_NUMBER}.json
```

## Step 7: Cleanup

```bash
# Remove workspace
rm -rf "$WORKSPACE"

# Deactivate virtualenv (if used)
deactivate 2>/dev/null || true
```

## Step 8: Provide Summary

```
🧪 Test Execution Complete

Status: ✅ PASSED (or ❌ FAILED, ⏱️ TIMEOUT)
Tests: 23 passed, 0 failed, 1 skipped
Duration: 45 seconds (limit: 600s)

<If failed, show top 3 failures>

Failures:
1. test_validate_token_expired - AssertionError: Expected False, got True
2. test_auth_race_condition - Timeout waiting for lock
3. test_session_cleanup - Database connection not closed

Results saved to: $OUTPUT_DIR/test-results-123.json
```

## Safety Features

These are the guarantees the runner actually enforces. Read the caveats — several
controls are best-effort and OS-dependent, not hard sandboxing.

### Enforced
- ✅ **Wall-clock timeout** — each run is wrapped in `timeout` (10 min tests,
  5 min dependency install); the process is killed when it expires.
- ✅ **Isolated workspace** — code is checked out into a fresh `mktemp -d`
  directory; cleaned up after the run.
- ✅ **Dangerous-pattern denylist** — the test command is grepped for a small set
  of destructive patterns (`rm -rf`, `dd if=`, `mkfs`, `ssh`, privileged Docker,
  production URLs). This is **defense-in-depth only**, not a real sandbox: a
  denylist cannot catch every dangerous command, so never rely on it alone.

### Best-effort (OS-dependent, not guaranteed)
- ⚠️ **Memory limit (`ulimit -v`, ~2GB)** — a soft per-process address-space
  cap. Behavior varies by platform and does not bound child processes reliably.
- ⚠️ **Single-file size limit (`ulimit -f`, ~1GB)** — limits the size of any one
  file written, **not** total disk usage. No portable total-disk cap exists.

### Not enforced
- ❌ **Network isolation** — attempted via `unshare --net` on Linux (requires
  privileges/namespaces) and **skipped entirely on macOS**. Do not assume tests
  run without network access; only production-URL patterns in the command are
  blocked, and the workload itself may still make outbound connections.
- ❌ **CPU-core / CPU-seconds limit** — not set; wall-clock `timeout` is the only
  time bound.

## When Tests Are NOT Run

Skip test execution if:
- `test_setup.can_run_safely` is false
- No test framework detected
- Test command contains dangerous patterns
- PR requires external services (databases, APIs)
- Integration/E2E tests detected (too slow/unsafe)

**In these cases:**
```
⚠️ Test Execution Skipped

Reason: <specific reason>
Recommendation: Run tests manually with: <command>
```

## Error Handling

**If checkout fails:**
```
Error: Could not checkout PR
- Check permissions
- Verify PR is open
- Try: gh pr checkout <number>
```

**If dependency install fails:**
```
Error: Dependency installation failed
- Check requirements file syntax
- Verify package availability
- Review install logs
```

**If tests crash:**
```
Error: Test execution crashed
- Check test configuration
- Review test output for errors
- Verify dependencies installed correctly
```

**If timeout:**
```
⏱️ Tests timed out after 10 minutes
- Tests may be too slow for automated execution
- Consider optimizing test suite
- Run manually for full results
```

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

## Notes

- Only runs unit tests (not integration/e2e)
- Tests run in isolated temporary directory
- All output captured for analysis
- Workspace cleaned up after execution
- Safe by default - skips if any doubt about safety
- Never modifies user's working directory
- Can be run standalone or via review
