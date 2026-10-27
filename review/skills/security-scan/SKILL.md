---
name: security-scan
description: Run security scans using semgrep, linters, and dependency checkers to find vulnerabilities, including OWASP authz/IDOR, business-logic abuse, SSRF, and PII-in-logs. Use when reviewing a PR that touches security-sensitive code or you need to surface injection, crypto, secrets, or dependency CVE risks.
allowed-tools: Bash Read Grep Glob
---

# Security Scanner

Security-scan PR changes using multiple tools: semgrep for code patterns, language-specific linters for vulnerabilities, dependency checkers for known CVEs.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Output dir. Defaults to private `mktemp -d`.
- **Analysis JSON**: From `analyze` skill at `$OUTPUT_DIR/pr-analysis-<number>.json`

## Outputs

Writes security findings to `$OUTPUT_DIR/security-scan-<PR_NUMBER>.json`:
```json
{
  "pr_number": 123,
  "scan_timestamp": "2025-02-07T10:30:00Z",
  "security_sensitive": true,
  "findings": {
    "critical": 2,
    "high": 3,
    "medium": 5,
    "low": 8,
    "total": 18
  },
  "by_category": {
    "injection": 2,
    "crypto": 1,
    "auth": 2,
    "business_logic": 0,
    "ssrf": 0,
    "pii_logging": 0,
    "secrets": 0,
    "dependencies": 5,
    "code_quality": 8
  },
  "critical_findings": [
    {
      "severity": "critical",
      "category": "injection",
      "rule": "sql-injection",
      "file": "src/db.py",
      "line": 45,
      "code": "cursor.execute(f\"SELECT * FROM users WHERE id={user_id}\")",
      "message": "SQL injection vulnerability - user input not sanitized",
      "fix": "Use parameterized queries: cursor.execute(\"SELECT * FROM users WHERE id=?\", (user_id,))",
      "cwe": "CWE-89"
    }
  ],
  "dependency_vulnerabilities": [
    {
      "package": "requests",
      "version": "2.25.0",
      "vulnerability": "CVE-2023-32681",
      "severity": "high",
      "fixed_version": "2.31.0",
      "description": "Unintended leak of Proxy-Authorization header"
    }
  ],
  "secrets_found": [],
  "tools_used": ["semgrep", "bandit", "npm-audit"],
  "scan_duration_seconds": 12
}
```

## Prerequisites

**Required tools (install if missing):**
```bash
# Semgrep (universal scanner)
pip install semgrep
# or: brew install semgrep

# Python: bandit
pip install bandit

# JavaScript: npm audit (built-in)
# Go: gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Ruby: brakeman
gem install brakeman
```

## Step 0: Parse Arguments

Extract PR URL and output dir from arguments:

```bash
PR_URL="$1"
# Default to a private per-run temp dir when run standalone (no OUTPUT_DIR passed)
OUTPUT_DIR="${2:-$(mktemp -d -t pr-review-XXXXXX)}"

# Extract PR number for filename
PR_NUMBER=$(echo "$PR_URL" | grep -oE 'pull/[0-9]+' | grep -oE '[0-9]+')

echo "Output directory: $OUTPUT_DIR" >&2
echo "PR number: $PR_NUMBER" >&2
```

**Load PR analysis:**
```bash
cat "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
```

## Step 0b: Load anti-patterns

Read `references/anti-patterns.md` — it carries the OWASP dimensions to deepen
(authz/IDOR, business-logic abuse, SSRF, PII-in-logs) alongside the classics.

Also skim `shared/severity-rubric.md` for Clean Code blocking rules
(security-adjacent craft issues — swallowed auth errors, flag params disabling
authz — are blockers, not nits).

## Step 1: Check Tool Availability

Detect which security tools available:

```bash
# Universal
command -v semgrep >/dev/null && HAVE_SEMGREP=true

# Language-specific
if [ "$PRIMARY_LANG" = "python" ]; then
  command -v bandit >/dev/null && HAVE_BANDIT=true
  command -v safety >/dev/null && HAVE_SAFETY=true
fi

if [ "$PRIMARY_LANG" = "javascript" ]; then
  command -v npm >/dev/null && HAVE_NPM=true
  command -v yarn >/dev/null && HAVE_YARN=true
fi

if [ "$PRIMARY_LANG" = "go" ]; then
  command -v gosec >/dev/null && HAVE_GOSEC=true
fi

if [ "$PRIMARY_LANG" = "ruby" ]; then
  command -v brakeman >/dev/null && HAVE_BRAKEMAN=true
fi

if [ "$PRIMARY_LANG" = "java" ]; then
  command -v spotbugs >/dev/null && HAVE_SPOTBUGS=true
fi

# Rust: cargo tooling IS the scanner (semgrep's Rust coverage is thin).
if [ "$PRIMARY_LANG" = "rust" ]; then
  command -v cargo-audit >/dev/null   && HAVE_CARGO_AUDIT=true
  command -v cargo-deny  >/dev/null   && HAVE_CARGO_DENY=true
  command -v cargo-machete >/dev/null && HAVE_CARGO_MACHETE=true
  command -v cargo >/dev/null         && HAVE_CLIPPY=true   # cargo clippy
fi

# mac-ui: audit changed .ts against the framework's live authority docs.
USES_MAC_UI=$(jq -r '.uses_mac_ui // false' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" 2>/dev/null)
MAC_UI_REF_REPO=$(jq -r '.mac_ui_ref_repo // empty' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" 2>/dev/null)
```

**If no tools available:**
```
⚠️ Security scanning limited: No security tools installed
Recommend installing: semgrep (universal), <language-specific tool>
```

### 1.1 Gate the dependency audits on a changed manifest

A dependency audit reports the whole dependency tree's advisories, so it returns
the same findings on every PR against a branch, whether or not that PR touched a
dependency. Those findings are real but they are not this PR's, and the author
defers them round after round. Run the auditors only when the PR changes a
manifest or a lockfile.

```bash
# /review:review captures pr.diff and pr.files once for every pass; read them,
# never write them. Fetch only on a standalone run.
if [ ! -s "$OUTPUT_DIR/pr.diff" ]; then
  gh pr diff "$PR_URL" > "$OUTPUT_DIR/pr.diff"
  gh pr diff "$PR_URL" --name-only > "$OUTPUT_DIR/pr.files"
fi
MANIFEST_RE='(^|/)(package-lock\.json|package\.json|yarn\.lock|pnpm-lock\.yaml|requirements[^/]*\.txt|poetry\.lock|Pipfile\.lock|pyproject\.toml|Cargo\.lock|Cargo\.toml|go\.mod|go\.sum|Gemfile\.lock|pom\.xml|build\.gradle[^/]*)$'
if grep -qE "$MANIFEST_RE" "$OUTPUT_DIR/pr.files"; then
  AUDIT_DEPS=true
else
  AUDIT_DEPS=false
fi
```

When `AUDIT_DEPS=false`, skip Step 6 entirely, leave `dependency_vulnerabilities`
empty, omit the audit tools from `tools_used`, and say so in the Step 11 summary:

> Dependency audit skipped — no manifest or lockfile in this PR.

The code scanners (semgrep, bandit, gosec, clippy, the pattern catalogs) are
unaffected — they are scoped to changed files already.

### 1.2 Capture the diff for hunk scoping

`semgrep`, `bandit` and `gosec` report per file, not per hunk, so a thirty-line
change to a two-thousand-line module returns findings on all two thousand lines.
Scope them to the lines the PR added, using the `pr.diff` from 1.1.

```bash
FILTER="$CLAUDE_PLUGIN_ROOT/scripts/changed_lines.py"
```

If `$CLAUDE_PLUGIN_ROOT` is unset, Glob for `**/scripts/changed_lines.py`. A
bare relative path resolves against the **reviewed repo**, not this plugin.

Scoping is to **added** lines only. A hunk's context lines are unchanged code
that would have been flagged on the base branch too. A multi-line finding
survives if any line in its span was added, so a function-level rule still fires
when the PR touched one line inside it.

What this deliberately loses: a vulnerability the PR *exposed* without editing —
a new caller reaching an old unsanitized sink. The data-flow checks in Step 5 and
the bug-finder's sink tracing cover that class; these pattern scanners did not.

## Step 2: Run Semgrep (Universal Scanner)

Semgrep is language-agnostic, catches most common vulnerabilities:

```bash
semgrep \
  --config=auto \
  --json \
  --quiet \
  --timeout=60 \
  --max-memory=4096 \
  <changed_files> \
  | python3 "$FILTER" filter --diff "$OUTPUT_DIR/pr.diff" --tool semgrep \
  > "$OUTPUT_DIR"/semgrep-results.json
```

The filter prints its drop count to stderr. Report that count in Step 11 — a
large one means the PR touched a file that was already dirty, which is worth
knowing even though those findings are not this PR's.

**Rules to use:**
- `auto` - Auto-detect language, use appropriate rules
- `p/security-audit` - OWASP Top 10 patterns
- `p/secrets` - Detect hardcoded secrets
- `p/ci` - CI/CD security issues

**Parse semgrep output:**
```bash
# Extract findings by severity
jq '.results[] | select(.extra.severity == "ERROR")' "$OUTPUT_DIR"/semgrep-results.json  # Critical
jq '.results[] | select(.extra.severity == "WARNING")' "$OUTPUT_DIR"/semgrep-results.json  # High
jq '.results[] | select(.extra.severity == "INFO")' "$OUTPUT_DIR"/semgrep-results.json  # Medium
```

## Step 3: Run Language-Specific Scanners

### Python: Bandit

```bash
bandit -r <changed_python_files> -f json -ll \
  | python3 "$FILTER" filter --diff "$OUTPUT_DIR/pr.diff" --tool bandit \
  > "$OUTPUT_DIR"/bandit-results.json
```

**What bandit finds:**
- SQL injection (B608)
- Hardcoded passwords (B105, B106, B107)
- Use of `eval()` (B307)
- Use of `exec()` (B102)
- Insecure random (B311)
- Weak crypto (B303, B304, B305)

### Python: Safety (dependency checker)

```bash
if [ "$AUDIT_DEPS" = true ]; then
  safety check \
    --json \
    --file=requirements.txt \
    > "$OUTPUT_DIR"/safety-results.json 2>&1 || true
fi
```

### JavaScript/TypeScript: npm audit

```bash
if [ "$AUDIT_DEPS" = true ]; then
  if [ -f "package-lock.json" ]; then
    npm audit --json > "$OUTPUT_DIR"/npm-audit-results.json 2>&1 || true
  elif [ -f "yarn.lock" ]; then
    yarn audit --json > "$OUTPUT_DIR"/yarn-audit-results.json 2>&1 || true
  fi
fi
```

**Parse npm audit:**
```bash
# Extract high/critical vulnerabilities
jq '.vulnerabilities | to_entries[] | select(.value.severity == "high" or .value.severity == "critical")' "$OUTPUT_DIR"/npm-audit-results.json
```

### Go: gosec

```bash
gosec -fmt=json <changed_go_files> 2>/dev/null \
  | python3 "$FILTER" filter --diff "$OUTPUT_DIR/pr.diff" --tool gosec \
  > "$OUTPUT_DIR"/gosec-results.json || true   # findings are not an error
```

### Ruby: Brakeman

```bash
# Scan Rails app
brakeman \
  --format json \
  --output "$OUTPUT_DIR"/brakeman-results.json \
  --quiet \
  --no-pager
```

### Java: SpotBugs

```bash
# Scan Java bytecode (requires compilation)
spotbugs \
  -textui \
  -xml:withMessages \
  -output "$OUTPUT_DIR"/spotbugs-results.xml \
  <class_files>
```

### Rust: cargo tooling + correctness/PHI catalog

When `PRIMARY_LANG=rust`, cargo tooling replaces the (Rust-blind) generic
scanners. Read `references/rust-security.md`, run its supply-chain commands
(`cargo audit` and `cargo deny` only when `AUDIT_DEPS=true`; `cargo machete` and
`cargo clippy -- -D warnings` or `just clippy` always), then grep changed `.rs` (non-test) for its correctness/PHI
pattern catalog — secret/PHI behind `#[derive(Debug)]`, sensitive values in
logs, blank-env `Some("")`, silent enum fallback, `reqwest::Client::new()`
without a timeout, `unwrap`/`expect`/`panic!`/`unsafe` in non-test code.
These classes recur on this codebase; report them as a Rust
cluster.

### mac-ui: idiom & security audit (dynamic)

When `USES_MAC_UI=true`, read `references/mac-ui-audit.md` and follow it: fetch
mac-ui's live authority docs from `$MAC_UI_REF_REPO` via `gh api` (it may be
private), then audit changed `mac-*` `.ts` against the fetched Violation
Catalog, security-bearing violations such as unescaped HTML sinks first.
Fetch at HEAD; never audit from memory, because the framework changes.

## Step 4: Detect Hardcoded Secrets

### 4.1 Pattern-Based Detection

Look for common secret patterns in diff.

```bash
grep -E "(password|secret|key|token|api_key)" "$OUTPUT_DIR/pr.diff" | grep -v "test\|example"
```

**Patterns to detect:**

**API Keys:**
```regex
[A-Za-z0-9]{32,}  # Generic 32+ char alphanumeric
sk_live_[A-Za-z0-9]+  # Stripe
AKIA[A-Z0-9]{16}  # AWS access key
```

**Passwords:**
```regex
password\s*=\s*["'][^"']+["']
pwd\s*=\s*["'][^"']+["']
```

**Private Keys:**
```regex
-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----
```

**Tokens:**
```regex
ghp_[A-Za-z0-9]{36}  # GitHub Personal Access Token
gho_[A-Za-z0-9]{36}  # GitHub OAuth Token
```

### 4.2 Entropy-Based Detection

High-entropy strings (likely secrets).

```bash
# Find strings with high entropy (randomness)
# Entropy > 4.5 = likely secret
grep -oE '[A-Za-z0-9]{20,}' <changed_files> | while read string; do
  entropy=$(calculate_entropy "$string")
  if [ "$entropy" > "4.5" ]; then
    echo "Potential secret: $string (entropy: $entropy)"
  fi
done
```

## Step 5: Scan for Common Vulnerabilities

Read `references/common-vulnerabilities.md` before grepping changed files for injection, auth, crypto patterns per language. Carry the Step 0b anti-patterns through this grep — the OWASP deepen dimensions are the ones these greps historically miss.

## Step 6: Analyze Dependencies

**Skip this step entirely when `AUDIT_DEPS=false`** (Step 1.1).

Read `references/dependency-analysis.md` before checking known CVEs and outdated packages per language.

Emit **one finding per `(package, advisory id)`**. Two routes to the same
advisory — `safety` and `pip-audit`, `npm audit` and `cargo deny` on a shared
transitive — are one finding, as are the many transitive paths a single advisory
reaches. Name the shortest path in `body` and give the count of the rest.

## Step 7: Categorize Findings

Read `references/finding-categories.md` and group findings by its categories — they are the keys of the `categories` counters in the output JSON.

## Step 8: Prioritize Findings

### 8.1 Severity Assignment

**Critical:**
- Remote code execution (RCE)
- SQL injection in production code
- Hardcoded production credentials
- Authentication bypass

**High:**
- XSS vulnerabilities
- Command injection
- Weak crypto in sensitive areas
- Dependency CVE with CVSS > 7.0

**Medium:**
- Missing input validation
- Information disclosure
- Insecure defaults
- Dependency CVE with CVSS 4.0-6.9

**Low:**
- Code quality issues
- Deprecated functions
- Missing error handling
- Dependency CVE with CVSS < 4.0

### 8.2 Context Adjustment

Adjust severity by context:

- **Increase if:**
  - Code handles user input
  - Code is in security-sensitive area (auth, payment, PII)
  - Finding is in public API
  - Production environment affected

- **Decrease if:**
  - Code is test-only
  - Finding is in unreachable code path
  - Already mitigated by other controls

## Step 9: Generate Fixes

Read `references/generate-fixes.md` before suggesting fix for each finding; contains bad/good code examples.

## Step 10: Generate Security Report JSON

Build JSON with `jq -n` so every PR-derived value (file paths, code snippets, messages) is safely escaped — pass numbers/arrays/objects with `--argjson`, plain strings with `--arg`. Never interpolate untrusted text into a heredoc. `*_JSON` variables below must already be valid JSON (build them with `jq`).

```bash
jq -n \
  --argjson pr_number "$PR_NUMBER" \
  --arg scan_timestamp "$(date -Iseconds)" \
  --argjson security_sensitive "$SECURITY_SENSITIVE" \
  --argjson critical "$CRITICAL_COUNT" \
  --argjson high "$HIGH_COUNT" \
  --argjson medium "$MEDIUM_COUNT" \
  --argjson low "$LOW_COUNT" \
  --argjson total "$TOTAL_COUNT" \
  --argjson by_category "$CATEGORIES_JSON" \
  --argjson critical_findings "$CRITICAL_FINDINGS_JSON" \
  --argjson high_findings "$HIGH_FINDINGS_JSON" \
  --argjson dependency_vulnerabilities "$DEP_VULNS_JSON" \
  --argjson secrets_found "$SECRETS_JSON" \
  --argjson tools_used "$TOOLS_USED_JSON" \
  --argjson scan_duration_seconds "$DURATION" \
  '{
    pr_number: $pr_number,
    scan_timestamp: $scan_timestamp,
    security_sensitive: $security_sensitive,
    findings: {
      critical: $critical,
      high: $high,
      medium: $medium,
      low: $low,
      total: $total
    },
    by_category: $by_category,
    critical_findings: $critical_findings,
    high_findings: $high_findings,
    dependency_vulnerabilities: $dependency_vulnerabilities,
    secrets_found: $secrets_found,
    tools_used: $tools_used,
    scan_duration_seconds: $scan_duration_seconds
  }' > "$OUTPUT_DIR"/security-scan-${PR_NUMBER}.json
```

## Step 11: Provide Summary

```
🔒 Security Scan Complete

Findings:
  - 🔴 Critical: 2
  - 🟠 High: 3
  - 🟡 Medium: 5
  - 🟢 Low: 8

Top Issues:
  1. [CRITICAL] SQL injection in db.py:45
  2. [CRITICAL] Hardcoded API key in config.py:12
  3. [HIGH] requests 2.25.0 has CVE-2023-32681

Tools Used: semgrep, bandit, npm-audit
Scoped out: 14 findings outside the diff's changed lines
Dependency audit: skipped (no manifest in this PR)

Security Sensitive: Yes

Analysis saved to: $OUTPUT_DIR/security-scan-123.json

⚠️ Address critical and high findings before merge
```

## Error Handling and Notes

Read `references/error-handling-and-notes.md` when tools fail, no tools installed, no findings, or need scan caveats.
