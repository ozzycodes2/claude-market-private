---
name: test-gaps
description: Analyze test coverage and recommend new tests based on code changes. Use when reviewing a PR and you need to assess whether the changes are adequately tested.
allowed-tools: Bash Read Grep Glob
---

# Test Analysis

Analyzes test coverage for PR changes and recommends new tests based on what code was modified. Identifies untested code paths, missing test cases, and suggests specific test scenarios.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Directory for output files. Defaults to a private `mktemp -d` directory if not provided.
- **Analysis JSON**: From `analyze` skill at `<OUTPUT_DIR>/pr-analysis-<number>.json`

## Outputs

Writes test analysis to `<OUTPUT_DIR>/test-analysis-<PR_NUMBER>.json` with structure:
```json
{
  "pr_number": 123,
  "overall_coverage": {
    "changed_lines": 450,
    "tested_lines": 270,
    "coverage_percentage": 60,
    "target_percentage": 80
  },
  "test_files": {
    "found": ["tests/test_auth.py", "tests/test_api.py"],
    "missing": ["tests/test_models.py"],
    "modified": ["tests/test_auth.py"],
    "needs_update": ["tests/test_api.py"]
  },
  "coverage_by_file": [
    {
      "file": "src/auth.py",
      "changed_lines": 120,
      "tested_lines": 80,
      "coverage": 67,
      "status": "needs_improvement"
    }
  ],
  "untested_areas": [
    {
      "file": "src/auth.py",
      "function": "validate_token()",
      "lines": "45-67",
      "reason": "New function, no tests found",
      "priority": "high"
    }
  ],
  "recommended_tests": [
    {
      "priority": "high",
      "test_file": "tests/test_auth.py",
      "test_name": "test_validate_token_with_expired_token",
      "description": "Test that validate_token() rejects expired tokens",
      "code_under_test": "src/auth.py:validate_token()",
      "test_case": "Given an expired token, when validate_token() is called, then it should return False and log warning"
    }
  ],
  "test_quality": {
    "has_edge_cases": false,
    "has_error_handling": true,
    "has_integration_tests": false,
    "needs_improvement": ["Add edge case tests", "Add integration tests"]
  }
}
```

## Prerequisites

Run `analyze` first:
```bash
# This skill depends on analysis JSON
analyze https://github.com/org/repo/pull/123
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
```

## Step 1: Load PR Analysis

Read the analysis JSON:
```bash
cat "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
```

Extract:
- `changes.files` - All changed files
- `change_categories.code` - Code files (not tests/docs)
- `change_categories.tests` - Test files
- `test_setup.framework` - Test framework to use
- `languages.primary` - Primary language

## Step 2: Identify Test Files

### 2.1 Find Existing Test Files

**Pattern matching by language:**

**Python:**
- `test_*.py` or `*_test.py`
- Files in `tests/`, `test/` directories

**JavaScript/TypeScript:**
- `*.test.js`, `*.test.ts`, `*.spec.js`, `*.spec.ts`
- Files in `__tests__/`, `test/` directories

**Go:**
- `*_test.go`

**Java:**
- `*Test.java`, `*Tests.java`
- Files in `src/test/` directory

**Ruby:**
- `*_spec.rb`
- Files in `spec/` directory

**Rust:** unit tests are IN-FILE in a `#[cfg(test)] mod tests` block in the same
`.rs` (not a separate `test_*` file); integration tests are in the crate's
`tests/`. The file-convention mapping below does not apply — read
`references/rust-tests.md` and map changed items to `#[test]`/`#[tokio::test]`
by symbol, use `cargo-llvm-cov`/`just coverage` for real coverage against the
repo's own `--fail-under-lines` gate, and name untested error arms/variants and
`from_env` branches explicitly.

**mac-ui / Web Components:** when `analyze` set `uses_mac_ui: true`, read
`references/mac-ui-tests.md` and audit changed test files against mac-ui's
**live** `docs/ai-testing-guide.md` rubric (fetched via `gh api` — it changes),
not a generic heuristic.

```bash
# Find test files in PR
gh pr diff <PR_URL> --name-only | grep -E "(test_|_test\.|\.test\.|\.spec\.|_spec\.|mod tests|#\[test\])"
USES_MAC_UI=$(jq -r '.uses_mac_ui // false' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" 2>/dev/null)
MAC_UI_REF_REPO=$(jq -r '.mac_ui_ref_repo // "vlognow/mac-ui"' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" 2>/dev/null)
```

### 2.2 Map Code Files to Test Files

For each code file changed, find corresponding test file:

**Convention mapping:**
- `src/auth.py` → `tests/test_auth.py`
- `lib/api.js` → `__tests__/api.test.js`
- `pkg/handler.go` → `pkg/handler_test.go`
- `com/example/User.java` → `com/example/UserTest.java`

```bash
# For each code file, check if test exists
for code_file in $CODE_FILES; do
  # Derive test file name
  test_file=$(derive_test_filename "$code_file")

  if [ -f "$test_file" ]; then
    echo "✓ Test exists: $test_file"
  else
    echo "✗ Missing test: $test_file"
  fi
done
```

## Step 3: Analyze Changed Functions/Classes

### 3.1 Extract Changed Code Blocks

```bash
# Get diff with function context
gh pr diff <PR_URL> --unified=10
```

Parse diff to identify:
- New functions/methods (lines starting with `+def`, `+function`, `+func`, `+public`)
- Modified functions (changes within function body)
- Deleted functions (lines starting with `-def`, etc.)

### 3.2 Detect Untested Code

For each new/modified function:
1. Search test files for references to that function name
2. If not found → **untested**
3. If found → **tested** (but check if tests cover new behavior)

**Example - Python:**
```bash
# Check if function is tested
function_name="validate_token"
grep -r "def test.*${function_name}" tests/ || echo "UNTESTED: $function_name"
```

**Example - JavaScript:**
```bash
# Check if function is tested
function_name="validateToken"
grep -r "test.*${function_name}\|it.*${function_name}" __tests__/ || echo "UNTESTED: $function_name"
```

## Step 4: Estimate Coverage

> **Rust:** skip the heuristic below — run `cargo llvm-cov`/`just coverage` for
> real per-file coverage when the suite is runnable (see `references/rust-tests.md`),
> and report the repo's own threshold as the target.

### 4.1 Count Changed Lines vs Tested Lines

**Changed lines:**
```bash
# Lines added (not comments, not blank)
gh pr diff <PR_URL> | grep "^+" | grep -v "^+++" | grep -v "^\+\s*$" | grep -v "^\+\s*#" | wc -l
```

**Tested lines (heuristic):**
- If function has test: Count 70% of function lines as "tested"
- If function has no test: Count 0% as "tested"
- If function modified and test modified: Count 80% as "tested"

**Coverage percentage:**
```
coverage = (tested_lines / changed_lines) * 100
```

**Coverage assessment:**
- 80%+ → ✅ Good
- 60-79% → ⚠️ Needs improvement
- <60% → ❌ Poor

## Step 5: Analyze Test Quality

### 5.1 Check for Common Test Patterns

**Good patterns (look for these):**
- **Edge cases**: Tests with "empty", "null", "invalid", "boundary"
- **Error handling**: Tests with "error", "exception", "throws", "fails"
- **Integration**: Tests with "integration", "e2e", "end-to-end"
- **Mocking**: Tests with "mock", "stub", "fake"

**Missing patterns (note if absent):**
- No edge case tests
- No error handling tests
- No integration tests
- No negative test cases

### 5.2 Identify Test Smells

**Anti-patterns to flag:**
- Tests that don't assert anything (no `assert`, `expect`, `verify`)
- Tests with hardcoded values (dates, IDs, URLs)
- Tests that sleep/wait (indicates flaky test)
- Tests with no description/docstring

## Step 6: Generate Test Recommendations

For each untested or under-tested area, generate specific test recommendations:

### 6.1 Recommendation Template

```json
{
  "priority": "high|medium|low",
  "test_file": "path/to/test_file",
  "test_name": "test_function_with_scenario",
  "description": "What this test should verify",
  "code_under_test": "src/module.py:function_name()",
  "test_case": "Given X, when Y, then Z",
  "example_code": "# Optional code snippet"
}
```

### 6.2 Priority Rubric

**High priority:**
- New functions in security-sensitive code (auth, crypto, DB)
- Functions with no tests
- Critical business logic
- Public APIs

**Medium priority:**
- Modified functions with outdated tests
- Internal helper functions
- Configuration/setup code

**Low priority:**
- Getters/setters
- Simple formatters
- UI/presentation code (if backend)

### 6.3 Generate Test Cases

For each untested function, generate 2-3 test cases:

**1. Happy Path**
- Normal input → expected output
- Example: `test_validate_token_with_valid_token()`

**2. Error Handling**
- Invalid input → proper error
- Example: `test_validate_token_with_expired_token()`

**3. Edge Cases** (if applicable)
- Boundary conditions → correct behavior
- Example: `test_validate_token_with_empty_string()`

**Test case format (Given-When-Then):**
```
Given: [Initial state/input]
When: [Action performed]
Then: [Expected outcome]
```

## Step 7: Recommend Test Framework Setup

If no tests exist yet, recommend setup:

**Python (pytest):**
```bash
# Add to requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0

# Create tests/ directory
mkdir tests
touch tests/__init__.py
touch tests/conftest.py

# Example test file
cat > tests/test_example.py <<EOF
import pytest
from src.module import function

def test_function_happy_path():
    result = function("input")
    assert result == "expected"
EOF
```

**JavaScript (jest):**
```bash
# Add to package.json
npm install --save-dev jest @testing-library/jest-dom

# Create jest.config.js
npx jest --init

# Example test file
cat > __tests__/example.test.js <<EOF
import { function } from '../src/module';

describe('function', () => {
  test('happy path', () => {
    const result = function('input');
    expect(result).toBe('expected');
  });
});
EOF
```

**Go:**
```bash
# Tests are in same package with _test.go suffix
cat > pkg_test.go <<EOF
package pkg

import "testing"

func TestFunction(t *testing.T) {
    result := Function("input")
    if result != "expected" {
        t.Errorf("got %v, want %v", result, "expected")
    }
}
EOF
```

## Step 8: Check Test File Updates Needed

For existing test files, check if they need updates:

### 8.1 Modified Code Without Modified Tests

```bash
# Find code files that changed
code_files=$(gh pr diff <PR_URL> --name-only | grep -v test)

# For each code file, check if corresponding test was also modified
for code_file in $code_files; do
  test_file=$(derive_test_filename "$code_file")

  if git diff --name-only HEAD origin/main | grep -q "$test_file"; then
    echo "✓ Test updated: $test_file"
  else
    echo "⚠ Test not updated for: $code_file"
  fi
done
```

### 8.2 Changed Function Signatures

Look for:
- Added parameters → Tests need new parameter values
- Removed parameters → Tests need to remove parameters
- Changed return type → Tests need updated assertions

**Example detection (Python):**
```bash
# Find function signature changes
git diff HEAD origin/main -- "$code_file" | grep "^-def\|^+def"
```

## Step 9: Generate Analysis JSON

Combine all findings.

Build the JSON with `jq -n` so every PR-derived value is safely escaped — pass numbers/arrays/objects with `--argjson` and plain strings with `--arg`. Never interpolate untrusted text directly into a heredoc. The `*_JSON` variables below must already be valid JSON (e.g. arrays built with `jq`).

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --argjson changed_lines "$CHANGED_LINES" \
  --argjson tested_lines "$TESTED_LINES" \
  --argjson coverage_percentage "$COVERAGE_PCT" \
  --arg status "$COVERAGE_STATUS" \
  --argjson found "$TEST_FILES_FOUND_JSON" \
  --argjson missing "$TEST_FILES_MISSING_JSON" \
  --argjson modified "$TEST_FILES_MODIFIED_JSON" \
  --argjson needs_update "$TEST_FILES_NEED_UPDATE_JSON" \
  --argjson untested_areas "$UNTESTED_AREAS_JSON" \
  --argjson recommended_tests "$RECOMMENDED_TESTS_JSON" \
  --argjson has_edge_cases "$HAS_EDGE_CASES" \
  --argjson has_error_handling "$HAS_ERROR_HANDLING" \
  --argjson has_integration_tests "$HAS_INTEGRATION_TESTS" \
  --argjson needs_improvement "$IMPROVEMENTS_JSON" \
  '{
    pr_number: $pr_number,
    overall_coverage: {
      changed_lines: $changed_lines,
      tested_lines: $tested_lines,
      coverage_percentage: $coverage_percentage,
      target_percentage: 80,
      status: $status
    },
    test_files: {
      found: $found,
      missing: $missing,
      modified: $modified,
      needs_update: $needs_update
    },
    untested_areas: $untested_areas,
    recommended_tests: $recommended_tests,
    test_quality: {
      has_edge_cases: $has_edge_cases,
      has_error_handling: $has_error_handling,
      has_integration_tests: $has_integration_tests,
      needs_improvement: $needs_improvement
    }
  }' > "$OUTPUT_DIR/test-analysis-${PR_NUMBER}.json"
```

## Step 10: Provide Summary

Display human-readable summary:

```
✅ Test Analysis Complete

Coverage: 60% (270/450 lines)
Target: 80%
Status: ⚠️ Needs Improvement

Test Files:
  - Found: 2
  - Missing: 1
  - Need updates: 1

Untested Areas (3):
  - src/auth.py:validate_token() [HIGH]
  - src/api.py:handle_request() [MEDIUM]
  - src/utils.py:format_date() [LOW]

Recommended Tests (5):
  - test_validate_token_with_expired_token [HIGH]
  - test_validate_token_with_invalid_signature [HIGH]
  - test_handle_request_with_missing_auth [MEDIUM]
  - test_handle_request_with_timeout [MEDIUM]
  - test_format_date_with_invalid_format [LOW]

Test Quality:
  ✓ Has error handling tests
  ✗ Missing edge case tests
  ✗ Missing integration tests

Analysis saved to: $OUTPUT_DIR/test-analysis-123.json
```

## Error Handling

**If analyze JSON not found:**
```
Error: Run analyze first
Example: analyze <PR_URL>
```

**If no code changes found:**
```
Info: PR contains only documentation/config changes
Test analysis skipped
```

**If analysis incomplete:**
- Generate JSON with available data
- Mark missing sections as `null`
- Note which analysis steps failed

## Notes

- This skill only ANALYZES tests, it doesn't run them (that's run-tests)
- Recommendations are heuristic-based (not code coverage tool)
- Works best when test file naming conventions are followed
- Can be run standalone or as part of review
- Output designed for both human reading and machine consumption
