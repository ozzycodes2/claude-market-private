# Security finding categories

The `categories` counters in `security-scan-<PR_NUMBER>.json` use these keys.

**Injection:**
- SQL injection
- Command injection
- XSS
- Path traversal

**Authentication/Authorization:**
- Missing authentication
- IDOR / missing object-level authorization
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

**Business Logic (`business_logic`):**
- Workflow step skipping / race-to-privilege
- Quota, coupon, or rate-limit bypass via parallel requests
- State-machine transitions not enforced server-side

**SSRF (`ssrf`):**
- User-controlled URL fetches (webhooks, previews, importers)
- Access to private/metadata IP ranges
- Missing egress allowlists

**PII in Logs (`pii_logging`):**
- PII/secrets in logs, metrics labels, traces, or exception messages
- Debug body dumps containing credentials/PHI

**Code Quality (Security-Adjacent):**
- Missing input validation
- Error information disclosure
- Insecure defaults
- Race conditions
