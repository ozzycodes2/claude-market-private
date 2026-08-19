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
- Some tools require dependencies installed
- False positives possible (review findings)
- Can be run standalone or via review
- Complements (not replaces) manual security review
