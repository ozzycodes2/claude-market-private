# Output examples

## Human-readable summary (`code-generation-<PR>-summary.md`)

Group by artifact type; show each generated snippet with its **Reason** and
**Confidence**. One entry per type shown:

````markdown
# Code Generation Summary

## Tests Generated: 3
### tests/test_auth.py
```python
def test_validate_token_expired():
    """Test validate_token with expired token."""
    token = generate_expired_token()
    assert validate_token(token, "test_secret") is False
```
**Reason:** Missing test for expired-token edge case · **Confidence:** High

---

## Docstrings Generated: 5
### src/auth.py:validate_token (line 45)
```python
"""Validates JWT authentication token.

Args:
    token (str): JWT token string to validate.
    secret (str): Secret key for signature verification.
Returns:
    bool: True if valid and not expired, else False.
Raises:
    ValueError: If token format is invalid.
"""
```
**Reason:** Function lacks documentation · **Confidence:** High

---

## CHANGELOG Entry: 1  (Keep a Changelog style)
```markdown
## [1.2.0] - 2025-02-07
### Added
- JWT authentication for API endpoints
### Security
- Token expiration checks; login rate limiting
```
**Reason:** No CHANGELOG entry for this PR · **Confidence:** Medium

---

## API Documentation: 2 sections
### docs/api/auth.md — POST /api/auth/login
(use the endpoint template in `references/generation-templates.md`)
**Reason:** New endpoint not documented · **Confidence:** Medium
````

## CHANGELOG version bump

- **MAJOR** (x.0.0): breaking/API changes (`breaking_changes` in analysis JSON)
- **MINOR** (0.x.0): new non-breaking features
- **PATCH** (0.0.x): fixes/docs only

## Skipped-item record

```json
{ "skipped": [ {
  "file": "src/payment.rs", "function": "process_payment",
  "reason": "Too complex for automatic test generation",
  "recommendation": "Write tests manually with fakes for external services"
} ] }
```
