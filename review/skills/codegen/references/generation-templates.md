# Generation templates by language

Skeletons for the low-risk artifacts codegen produces. Fill placeholders from
the PR; keep to the SKILL.md rules (happy + ≤2 edge cases, <20-line functions,
no external deps).

## Tests

**Python (pytest)** — Arrange/Act/Assert with a Given/When/Then docstring:
```python
def test_<fn>_<scenario>():
    """Test <fn> <scenario>. Given <cond>, when <action>, then <result>."""
    email = "user@example.com"        # Arrange
    result = is_valid_email(email)    # Act
    assert result is True             # Assert
```
Generate the valid, invalid, and empty-string cases for a simple validator.

**JavaScript (jest)**
```javascript
describe('<fn>', () => {
  it('should <behavior>', () => {
    const input = <data>;
    expect(functionName(input)).toBe(<expected>);
  });
});
```

**Go**
```go
func Test<Fn>_<Scenario>(t *testing.T) {
    input, expected := <data>, <expected>
    if got := FunctionName(input); got != expected {
        t.Errorf("got %v, want %v", got, expected)
    }
}
```

**Java (JUnit)**
```java
@Test public void test<Fn>_<Scenario>() {
    assertEquals(<expected>, functionName(<input>));
}
```

**Rust** — unit tests are IN-FILE in a `#[cfg(test)] mod tests` block in the
same file as the code (not a separate `test_*` file). Use `#[tokio::test]` for
async. Test modules carry `#![allow(clippy::unwrap_used)]`; do not add `unwrap`
outside them.
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn <fn>_<scenario>() {
        assert_eq!(is_valid(<input>), <expected>);
    }
}
```
Prefer generating the missing *branch* cases a coverage gap named (e.g. the
unset/blank/invalid arms of a `from_env`), not just a happy path.

## Docstrings

**Python (Google style)** — `Args:`/`Returns:`/`Raises:`, active voice.
**JavaScript (JSDoc)** — `@param {type}`, `@returns {type}`, `@throws`.
**Go** — `// FunctionName <does X>.` leading comment.
**Java (Javadoc)** — `@param`/`@return`/`@throws`.
**Rust** — `///` doc comments; `# Errors` section for `Result` returns,
`# Panics` if it can panic. Match the crate's existing density; don't
re-derive internals.

## API endpoint doc (OpenAPI-style markdown)

```markdown
## POST /api/endpoint
Brief description.

### Request
**Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
**Body:** ```json { "field1": "string", "field2": 123 } ```

### Response
**Success (200):** ```json { "status": "success", "data": {} } ```
**Error (4xx):** ```json { "status": "error", "message": "..." } ```

### Errors
- `400` invalid input · `401` missing/invalid token · `500` server error
```

> **mac-ui:** codegen does not hand-write mac-ui component code. If a doc/test
> for a `mac-*` component is needed, defer to the live mac-ui authority docs
> (see the `docs-drift` mac-ui references) rather than templating a
> component from memory — the framework changes.
