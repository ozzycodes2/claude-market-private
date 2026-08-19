## When Tests Are NOT Run

Skip test execution if:
- `test_setup.can_run_safely` is false
- No test framework detected
- Test command contains dangerous patterns
- PR requires external services (databases, APIs)
- Integration/E2E tests detected (too slow/unsafe)

**In these cases, emit:**
```
⚠️ Test Execution Skipped

Reason: <specific reason>
Recommendation: Run tests manually with: <command>
```
