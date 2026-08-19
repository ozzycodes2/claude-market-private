---
name: security-scan
description: Run security scans using semgrep, linters, and dependency checkers to find vulnerabilities. Use when reviewing a PR that touches security-sensitive code or you need to surface injection, crypto, secrets, or dependency CVE risks.
allowed-tools: Bash Read Grep Glob
disable-model-invocation: true
---

# Security Scanner

Runs comprehensive security scanning on PR changes using multiple tools: semgrep for code patterns, language-specific linters for vulnerabilities, and dependency checkers for known CVEs.

## Inputs

- **PR URL**: Full GitHub/Enterprise PR URL
- **OUTPUT_DIR** (optional): Directory for output files. Defaults to a private `mktemp -d` directory if not provided.
- **Analysis JSON**: From `analyze` skill at `$OUTPUT_DIR/pr-analysis-<number>.json`

## Outputs

Writes security findings to `$OUTPUT_DIR/security-scan-<PR_NUMBER>.json` with structure:
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

**Load PR analysis:**
```bash
cat "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json"
```

## Step 1: Check Tool Availability

Detect which security tools are available:

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
MAC_UI_REF_REPO=$(jq -r '.mac_ui_ref_repo // "vlognow/mac-ui"' "$OUTPUT_DIR/pr-analysis-${PR_NUMBER}.json" 2>/dev/null)
```

**If no tools available:**
```
⚠️ Security scanning limited: No security tools installed
Recommend installing: semgrep (universal), <language-specific tool>
```

## Step 2: Run Semgrep (Universal Scanner)

Semgrep is language-agnostic and catches most common vulnerabilities:

```bash
# Run semgrep with security rules
semgrep \
  --config=auto \
  --json \
  --quiet \
  --timeout=60 \
  --max-memory=4096 \
  <changed_files> \
  > "$OUTPUT_DIR"/semgrep-results.json
```

**Rules to use:**
- `auto` - Auto-detect language and use appropriate rules
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
# Scan changed Python files
bandit \
  -r <changed_python_files> \
  -f json \
  -o "$OUTPUT_DIR"/bandit-results.json \
  -ll  # Low confidence = low severity
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
# Check for vulnerable dependencies
safety check \
  --json \
  --file=requirements.txt \
  > "$OUTPUT_DIR"/safety-results.json 2>&1 || true
```

### JavaScript/TypeScript: npm audit

```bash
# Check for vulnerable dependencies
if [ -f "package-lock.json" ]; then
  npm audit --json > "$OUTPUT_DIR"/npm-audit-results.json 2>&1 || true
elif [ -f "yarn.lock" ]; then
  yarn audit --json > "$OUTPUT_DIR"/yarn-audit-results.json 2>&1 || true
fi
```

**Parse npm audit:**
```bash
# Extract high/critical vulnerabilities
jq '.vulnerabilities | to_entries[] | select(.value.severity == "high" or .value.severity == "critical")' "$OUTPUT_DIR"/npm-audit-results.json
```

### Go: gosec

```bash
# Scan Go code
gosec \
  -fmt=json \
  -out="$OUTPUT_DIR"/gosec-results.json \
  <changed_go_files> \
  || true  # Don't fail on findings
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
scanners. Read `references/rust-security.md` and run its supply-chain commands
(`cargo audit`, `cargo deny`, `cargo machete`, `cargo clippy -- -D warnings` or
`just clippy`), then grep the changed `.rs` (non-test) for its correctness/PHI
pattern catalog — secret/PHI behind `#[derive(Debug)]`, sensitive values in
logs, blank-env `Some("")`, silent enum fallback, `reqwest::Client::new()`
without a timeout, and `unwrap`/`expect`/`panic!`/`unsafe` in non-test code.
These are the classes that recur on this codebase; report them as a Rust
cluster.

### mac-ui: idiom & security audit (dynamic)

When `USES_MAC_UI=true`, read `references/mac-ui-audit.md` and follow it: fetch
mac-ui's live authority docs from `$MAC_UI_REF_REPO` via `gh api` (the repo is
internal), then audit changed `mac-*` `.ts` against the fetched Violation
Catalog — `innerHTML = var` (XSS), raw `new CustomEvent` dispatch, unsafe casts.
Fetch at HEAD; never audit from memory, because the framework changes.

## Step 4: Detect Hardcoded Secrets

### 4.1 Pattern-Based Detection

Look for common secret patterns in diff:

```bash
gh pr diff <PR_URL> | grep -E "(password|secret|key|token|api_key)" | grep -v "test\|example"
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

High-entropy strings (likely secrets):

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

### 5.1 Injection Vulnerabilities

**SQL Injection:**
```bash
# Python
grep -n "execute.*f\".*SELECT\|execute.*%.*SELECT" <changed_files>

# JavaScript
grep -n "query.*\`.*SELECT\|query.*\${.*SELECT" <changed_files>

# Go
grep -n "Query.*fmt.Sprintf.*SELECT" <changed_files>
```

**Command Injection:**
```bash
# Look for shell execution with user input
grep -n "subprocess.call\|os.system\|exec\|shell=True" <changed_files>
```

**XSS (Cross-Site Scripting):**
```bash
# Look for unsafe HTML rendering
grep -n "innerHTML\|dangerouslySetInnerHTML\|document.write" <changed_files>
```

### 5.2 Authentication Issues

```bash
# Weak password hashing
grep -n "md5\|sha1\|base64" <changed_files>

# Missing authentication
grep -n "@app.route\|@router\|app.get\|app.post" <changed_files> | \
  grep -v "auth\|login\|@require"

# Hardcoded credentials
grep -n "password\s*=\|token\s*=\|api_key\s*=" <changed_files>
```

### 5.3 Crypto Issues

```bash
# Weak crypto
grep -n "DES\|RC4\|MD5\|SHA1" <changed_files>

# Insecure random
grep -n "random.random\|Math.random" <changed_files>
```

## Step 6: Analyze Dependencies

### 6.1 Check for Known Vulnerabilities

**Python:**
```bash
# Parse requirements.txt
grep -E "^[a-zA-Z0-9_-]+==\d" requirements.txt | while read dep; do
  package=$(echo $dep | cut -d'=' -f1)
  version=$(echo $dep | cut -d'=' -f3)

  # Check against vulnerability databases
  # (via safety check output from Step 3)
done
```

**JavaScript:**
```bash
# npm audit already checked in Step 3
# Parse results for critical/high
jq '.vulnerabilities | to_entries[] | select(.value.severity == "critical" or .value.severity == "high")' "$OUTPUT_DIR"/npm-audit-results.json
```

### 6.2 Check for Outdated Dependencies

```bash
# Python
pip list --outdated --format=json | jq '.[] | select(.latest_version > .version)'

# JavaScript
npm outdated --json

# Go
go list -u -m -json all | jq 'select(.Update != null)'
```

## Step 7: Categorize Findings

Group findings by category:

**Injection:**
- SQL injection
- Command injection
- XSS
- Path traversal

**Authentication/Authorization:**
- Missing authentication
- Weak password hashing
- Insecure session management
- Hardcoded credentials

**Cryptography:**
- Weak algorithms
- Insecure random
- Hardcoded keys
- Missing encryption

**Dependencies:**
- Known CVEs
- Outdated packages
- Unmaintained packages

**Code Quality (Security-Adjacent):**
- Missing input validation
- Error information disclosure
- Insecure defaults
- Race conditions

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

Adjust severity based on context:

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

For each finding, suggest a fix:

**SQL Injection:**
```python
# Bad
cursor.execute(f"SELECT * FROM users WHERE id={user_id}")

# Good
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
```

**Command Injection:**
```python
# Bad
os.system(f"ping {host}")

# Good
subprocess.run(["ping", host], capture_output=True, check=True)
```

**Weak Crypto:**
```python
# Bad
hashlib.md5(password.encode()).hexdigest()

# Good
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

## Step 10: Generate Security Report JSON

Build the JSON with `jq -n` so every PR-derived value (file paths, code snippets, messages) is safely escaped — pass numbers/arrays/objects with `--argjson` and plain strings with `--arg`. Never interpolate untrusted text directly into a heredoc. The `*_JSON` variables below must already be valid JSON (build them with `jq`).

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

Security Sensitive: Yes

Analysis saved to: $OUTPUT_DIR/security-scan-123.json

⚠️ Address critical and high findings before merge
```

## Error Handling

**If no security tools installed:**
```
⚠️ Limited security scanning (no tools found)
Install semgrep for comprehensive scanning: pip install semgrep
```

**If tools fail:**
- Continue with remaining tools
- Note which tools failed in report
- Don't fail entire scan

**If no findings:**
```
✅ No security issues found
(Scanned with: semgrep, bandit)
```

## Notes

- Scans only changed files (not entire codebase)
- Some tools require dependencies to be installed
- False positives possible (review findings)
- Can be run standalone or via review
- Complements (not replaces) manual security review
