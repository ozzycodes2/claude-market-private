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
