## Error Handling

**If checkout fails:**
```
Error: Could not checkout PR
- Check permissions
- Verify PR is open
- Try: gh pr checkout <number>
```

**If dependency install fails:**
```
Error: Dependency installation failed
- Check requirements file syntax
- Verify package availability
- Review install logs
```

**If tests crash:**
```
Error: Test execution crashed
- Check test configuration
- Review test output for errors
- Verify dependencies installed correctly
```

**If timeout:**
```
⏱️ Tests timed out after 10 minutes
- Tests may be too slow for automated execution
- Consider optimizing test suite
- Run manually for full results
```
