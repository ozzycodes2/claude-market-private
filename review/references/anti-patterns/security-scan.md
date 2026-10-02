# Anti-patterns — Security scan (OWASP deepen)

Read **only** this file for `security-scan`. Do not load other anti-pattern slices.

## Authz / IDOR (deepen — historically thin)

- Client-supplied object IDs without server-side ownership checks (IDOR)
- Function-level authz missing on new endpoints; default-allow
- Authz checks only in UI / gateway, not at handler
- Confused deputy / privilege escalation via role or tenant mix-up

## Business-logic abuse

- Workflow step skipping (e.g. pay without authorize, approve without review)
- Race-to-privilege / double-spend style flows
- Coupon/limit/quota bypass via parallel requests
- State machine transitions not enforced server-side

## SSRF / unsafe egress

- User-controlled URLs fetched server-side without allowlist / block private ranges
- Webhook/preview/importer features that hit internal metadata endpoints
- Redirect/DNS rebinding blind spots

## PII / secrets in logs & telemetry

- PII or secrets in logs, metrics labels, traces, exception messages
- Debug dumps of request bodies containing credentials/PHI
- Overly verbose error responses to clients

## Classic (keep scanning)

- String-built queries / command injection / XSS
- Secrets in repo
- Weak crypto / home-rolled crypto
- Debug endpoints left enabled
- Overly permissive CORS / authz
- Dependency CVEs on new/updated packages

## Clean Code (blocking when security-adjacent)

- Swallowed security errors (auth failures ignored)
- Boolean flag parameters that disable authz/validation on shared helpers
