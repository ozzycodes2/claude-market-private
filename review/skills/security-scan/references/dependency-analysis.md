## Step 6: Analyze Dependencies

**Runs only when `AUDIT_DEPS=true`** — the PR changed a manifest or lockfile.
Otherwise the audit reports the branch's standing advisories, not this PR's.

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
