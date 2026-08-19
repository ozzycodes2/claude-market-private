---
name: analyze
description: Analyze PR changes to detect languages, frameworks, test setup, and impact areas. Use when starting a PR review and you need to understand what changed before deeper analysis.
allowed-tools: Bash Read Grep Glob
disable-model-invocation: true
---

# Analyze PR Changes

Analyze a pull request: what changed, which languages/frameworks involved, how to test it, what impact areas need review.

**Foundation** for other review skills - produces structured analysis driving test recommendations, security scanning, documentation validation.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL (e.g., `https://github.com/org/repo/pull/123`)
- **OUTPUT_DIR** (optional): Output dir. Defaults to private `mktemp -d`.

## Outputs

Writes analysis to `<OUTPUT_DIR>/pr-analysis-<PR_NUMBER>.json`:
```json
{
  "pr": {
    "number": 123,
    "title": "Add user authentication",
    "url": "https://github.com/org/repo/pull/123",
    "base_branch": "main",
    "head_branch": "feature/auth",
    "author": "username",
    "state": "open"
  },
  "changes": {
    "files_changed": 15,
    "additions": 450,
    "deletions": 120,
    "files": ["src/auth.py", "tests/test_auth.py", "README.md"]
  },
  "languages": {
    "primary": "python",
    "detected": ["python", "javascript", "shell"],
    "confidence": {
      "python": 0.85,
      "javascript": 0.10,
      "shell": 0.05
    }
  },
  "frameworks": {
    "detected": ["django", "pytest", "npm"],
    "confidence": "high"
  },
  "test_setup": {
    "framework": "pytest",
    "test_command": "pytest",
    "test_files": ["tests/test_auth.py"],
    "config_files": ["pytest.ini", "setup.py"],
    "can_run_safely": true,
    "safety_notes": "Uses pytest with standard config"
  },
  "build_system": {
    "type": "python",
    "files": ["setup.py", "requirements.txt", "pyproject.toml"],
    "commands": {
      "install": "pip install -r requirements.txt",
      "test": "pytest",
      "lint": "flake8"
    }
  },
  "change_categories": {
    "code": ["src/auth.py", "src/api.py"],
    "tests": ["tests/test_auth.py"],
    "docs": ["README.md", "docs/auth.md"],
    "config": ["setup.py"],
    "infra": []
  },
  "impact_analysis": {
    "high_impact": ["authentication", "security"],
    "medium_impact": ["API endpoints"],
    "low_impact": ["documentation"],
    "breaking_changes": false
  },
  "security_sensitive": true,
  "needs_security_review": true,
  "uses_mac_ui": false,
  "mac_ui_ref_repo": "vlognow/mac-ui"
}
```

`uses_mac_ui` (see Step 4) tells `security-scan`, `test-gaps`, and `docs-drift`
to fetch mac-ui's live authority docs. `mac_ui_ref_repo` is the repo they fetch
from. Downstream skills read both from this JSON.

## Step 0: Parse Arguments

Extract PR URL and output dir from arguments:

```bash
PR_URL="$1"
# Default to a private per-run temp dir when run standalone (no OUTPUT_DIR passed)
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"

# Create output dir if missing
mkdir -p "$OUTPUT_DIR"

# Extract PR number for filename
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')

echo "Output directory: $OUTPUT_DIR" >&2
echo "PR number: $PR_NUMBER" >&2
```

## Step 1: Fetch PR Metadata

```bash
gh pr view "$PR_URL" --json number,title,url,baseRefName,headRefName,author,state,additions,deletions
```

Store in variables for later use.

## Step 2: Get Changed Files

```bash
gh pr diff <PR_URL> --name-only
```

Count files and categorize by type:
- **Code**: `.py`, `.js`, `.go`, `.java`, `.rb`, `.php`, `.ts`, `.tsx`, `.jsx`
- **Tests**: `test_*.py`, `*.test.js`, `*_test.go`, `Test*.java`
- **Docs**: `*.md`, `*.rst`, `*.txt`, `docs/`, `README*`
- **Config**: `*.json`, `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `Makefile`, `Dockerfile`
- **Infra**: `.github/`, `terraform/`, `k8s/`, `.circleci/`, `.gitlab-ci.yml`

## Step 3: Detect Languages

Analyze file extensions and count:
```bash
gh pr diff <PR_URL> --name-only | sed 's/.*\.//' | sort | uniq -c | sort -rn
```

**Primary language**: extension with most files
**Secondary languages**: extensions with >10% of files

**Language mapping:**
- `.py` → Python
- `.js`, `.jsx`, `.ts`, `.tsx` → JavaScript/TypeScript
- `.go` → Go
- `.java` → Java
- `.rb` → Ruby
- `.rs` → Rust
- `.php` → PHP
- `.c`, `.cpp`, `.cc` → C/C++

## Step 4: Detect Frameworks

Look for framework indicators in changed files or project root.

**Python:**
- Django: `django` in requirements.txt, `manage.py` exists
- Flask: `flask` in requirements.txt, `app.py` pattern
- FastAPI: `fastapi` in requirements.txt
- Pytest: `pytest` in requirements.txt or `pytest.ini` exists

**JavaScript:**
- React: `package.json` contains `"react"`
- Vue: `package.json` contains `"vue"`
- Angular: `package.json` contains `"@angular"`
- Express: `package.json` contains `"express"`
- Jest: `package.json` contains `"jest"`
- Mocha: `package.json` contains `"mocha"`

**Go:**
- `go.mod` exists → Go modules
- Standard library (no frameworks typically)

**Java:**
- Spring: `pom.xml` or `build.gradle` contains `spring`
- JUnit: `pom.xml` contains `junit`

**Rust:**
- Cargo: `Cargo.toml` exists (a `[workspace]` root marks a multi-crate workspace).
- Test runner: `cargo-nextest` if `.config/nextest.toml` exists or a `justfile`
  recipe runs `nextest`; else plain `cargo test`.
- Coverage: `cargo-llvm-cov` if a `just coverage`/`llvm-cov` recipe or
  `cargo-llvm-cov` in CI. Note any `--fail-under-lines` threshold (a hard gate).
- Supply-chain: `cargo-audit`, `cargo-deny` (`deny.toml`), `cargo-machete`.
- Command source: prefer a `justfile` — its `fmt`/`clippy`/`test`/`coverage`/`ci`
  recipes are what CI runs; record exact recipes, don't guess.

**mac-ui / Web Components (`@vlognow/mac-ui`):**
- Set `uses_mac_ui: true` when any of: `package.json` (root or a workspace
  package) depends on `@vlognow/mac-ui`/`mac-ui-react`/`mac-ui-utils`; a changed
  file registers or consumes a `mac-*` custom element (`customElements.define`,
  a `<mac-…>` tag, or an import from `@vlognow/mac-ui`).
- Monorepo: `lerna.json` + `packages/` → lerna workspace; `biome.json` → Biome
  lint/format; `vite.config.ts`/`web-dev-server-config.js` → Vite/WTR.
- Test runner: per-package `package.json` `test` script is authoritative
  (web-test-runner / vitest / jsdom); don't assume.

## Step 5: Analyze Test Setup

### 5.1 Find Test Framework

Look for:
- Python: `pytest.ini`, `tox.ini`, `setup.py` with test_suite
- JavaScript: `jest.config.js`, `package.json` "test" script
- Go: `*_test.go` files (standard testing)
- Java: `pom.xml` with surefire plugin, JUnit

### 5.2 Determine Test Command

**Python:**
```bash
# Check for common patterns
if [ -f "pytest.ini" ] || grep -q "pytest" requirements.txt; then
  echo "pytest"
elif [ -f "setup.py" ]; then
  echo "python setup.py test"
elif [ -f "Makefile" ] && grep -q "^test:" Makefile; then
  echo "make test"
fi
```

**JavaScript:**
```bash
# Check package.json for test script
if [ -f "package.json" ]; then
  npm run | grep "test"
  # Usually: npm test
fi
```

**Go:**
```bash
echo "go test ./..."
```

### 5.3 Safety Assessment

Determine if tests can run safely.

**Safe indicators:**
- Standard test frameworks (pytest, jest, go test, junit)
- No network calls in test names
- No database migrations
- Tests in isolated `tests/` or `__tests__/` directories

**Unsafe indicators:**
- Tests named `integration_test`, `e2e_test`
- Database setup required
- External service dependencies
- Docker/docker-compose required
- Tests modify filesystem outside /tmp

**Rust safety:** workspace suite is safe to run ONLY if it needs no live
infra. Mark unsafe when tests gate on env like `PGURL`, `KAFKA_BOOTSTRAP_SERVERS`,
`RUN_KAFKA_TESTS`, or a `just compose-up` stack — those need Postgres/Kafka/
LocalStack up, and coverage gates (`--fail-under-lines`) only pass with them
running. A unit-only subset (`cargo nextest run -E 'not test(/integration/)'`)
is usually safe; record it as the safe command.

**mac-ui safety:** web-component tests often need a browser/headless Chromium
(web-test-runner) that may be absent in a sandbox — default to unsafe unless the
package's `test` script is jsdom/vitest-only.

**Decision:**
```
can_run_safely = (
  uses_standard_framework AND
  no_external_dependencies AND
  no_destructive_operations AND
  execution_time_reasonable (<5min)
)
```

## Step 6: Detect Build System

Look for build config files.

**Python:**
- `setup.py` → setuptools
- `pyproject.toml` → modern Python (poetry, flit, hatch)
- `requirements.txt` → pip
- `Pipfile` → pipenv
- `Makefile` → make

**JavaScript:**
- `package.json` → npm/yarn
- `yarn.lock` → yarn
- `package-lock.json` → npm

**Go:**
- `go.mod` → Go modules
- `Makefile` → make

**Java:**
- `pom.xml` → Maven
- `build.gradle` → Gradle

**Rust:**
- `Cargo.toml` → cargo (workspace if `[workspace]`)
- `justfile` → task runner; its recipes are the source of truth for
  `install`/`test`/`lint`/`build` (mirror them into the commands map below)

**JS monorepo:**
- `lerna.json`/`pnpm-workspace.yaml`/`package.json` `workspaces` → monorepo;
  commands run per-package (`npm -w <pkg> test`)

**Extract common commands:**
```json
{
  "install": "<dependency install command>",
  "test": "<test execution command>",
  "lint": "<linter command>",
  "build": "<build command>"
}
```

## Step 7: Impact Analysis

### 7.1 Detect High-Impact Areas

Look for changes in sensitive files/patterns.

**Authentication/Security:**
- Files matching: `*auth*`, `*security*`, `*login*`, `*password*`, `*token*`
- Keywords in diff: "auth", "login", "password", "secret", "key"

**Database:**
- Files matching: `*migration*`, `*schema*`, `*model*`, `*db*`
- Keywords: "ALTER TABLE", "DROP", "CREATE TABLE"

**API:**
- Files matching: `*api*`, `*endpoint*`, `*route*`, `*handler*`
- Keywords: "GET", "POST", "PUT", "DELETE" in route definitions

**Configuration:**
- Files: `config/*`, `.env*`, `*.yaml`, `*.json` (in root or config dirs)

**Infrastructure:**
- Files: `Dockerfile`, `docker-compose.yml`, `k8s/*`, `terraform/*`

### 7.2 Detect Breaking Changes

Indicators:
- Major version bump in package file
- Removed or renamed functions/classes
- Changed function signatures
- Deleted files
- Database schema changes (DROP, ALTER)

Keywords in commits/PR title:
- "BREAKING", "breaking change", "incompatible", "removed", "deprecated"

## Step 8: Security Sensitivity Assessment

Determine if PR needs extra security scrutiny.

**High security sensitivity:**
- Changes authentication/authorization code
- Modifies database schemas
- Changes API endpoints
- Touches encryption/crypto code
- Modifies access control
- Updates dependencies with known vulnerabilities

**Markers:**
```python
security_sensitive = (
  affects_auth OR
  affects_database OR
  affects_api OR
  affects_crypto OR
  updates_security_deps
)
```

## Step 9: Generate Analysis JSON

Combine all findings into structured JSON, write to `$OUTPUT_DIR/pr-analysis-<PR_NUMBER>.json`.

Build JSON with `jq -n` so every PR-derived value is safely escaped — pass strings with `--arg`, numbers/booleans/arrays/objects with `--argjson`. Never interpolate untrusted text into a heredoc.

```bash
jq -n \
  --argjson pr "$PR_JSON" \
  --argjson changes "$CHANGES_JSON" \
  --argjson languages "$LANGUAGES_JSON" \
  --argjson frameworks "$FRAMEWORKS_JSON" \
  --argjson test_setup "$TEST_SETUP_JSON" \
  --argjson build_system "$BUILD_SYSTEM_JSON" \
  --argjson change_categories "$CHANGE_CATEGORIES_JSON" \
  --argjson impact_analysis "$IMPACT_ANALYSIS_JSON" \
  --argjson security_sensitive "$SECURITY_SENSITIVE" \
  --argjson needs_security_review "$NEEDS_SECURITY_REVIEW" \
  --argjson uses_mac_ui "${USES_MAC_UI:-false}" \
  --arg mac_ui_ref_repo "vlognow/mac-ui" \
  '{
    pr: $pr,
    changes: $changes,
    languages: $languages,
    frameworks: $frameworks,
    test_setup: $test_setup,
    build_system: $build_system,
    change_categories: $change_categories,
    impact_analysis: $impact_analysis,
    security_sensitive: $security_sensitive,
    needs_security_review: $needs_security_review,
    uses_mac_ui: $uses_mac_ui,
    mac_ui_ref_repo: $mac_ui_ref_repo
  }' > "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
```

## Step 10: Provide Summary to User

Display human-readable summary.

```
✅ PR Analysis Complete

PR: #123 - Add user authentication
Files changed: 15 (+450, -120)

Languages:
  - Python (85%)
  - JavaScript (10%)
  - Shell (5%)

Frameworks:
  - Django
  - Pytest

Test Setup:
  - Framework: pytest
  - Command: pytest
  - Can run safely: ✅
  - Test files: 1

Impact Areas:
  - 🔴 High: authentication, security
  - 🟡 Medium: API endpoints
  - 🟢 Low: documentation

Security: ⚠️  Requires security review

Analysis saved to: $OUTPUT_DIR/pr-analysis-123.json
```

## Error Handling

**If gh CLI fails:**
```
Error: Could not fetch PR. Check:
- gh is installed and authenticated
- PR URL is valid and accessible
- You have permissions to view this PR
```

**If analysis is incomplete:**
- Still generate JSON with available data
- Mark missing fields as `null`
- Note in summary which analysis steps failed

## Notes

- Does NOT modify code or run tests - only analyzes
- All analysis read-only (safe to run on any PR)
- Output JSON designed to be consumed by other skills
- Can be run standalone or as part of review
