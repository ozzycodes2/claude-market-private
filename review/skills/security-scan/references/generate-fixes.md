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
