## Step 7: Recommend Test Framework Setup

If no tests exist, recommend setup.

**Python (pytest):**
```bash
# Add to requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0

# Create tests/ directory
mkdir tests
touch tests/__init__.py
touch tests/conftest.py

# Example test file
cat > tests/test_example.py <<EOF
import pytest
from src.module import function

def test_function_happy_path():
    result = function("input")
    assert result == "expected"
EOF
```

**JavaScript (jest):**
```bash
# Add to package.json
npm install --save-dev jest @testing-library/jest-dom

# Create jest.config.js
npx jest --init

# Example test file
cat > __tests__/example.test.js <<EOF
import { function } from '../src/module';

describe('function', () => {
  test('happy path', () => {
    const result = function('input');
    expect(result).toBe('expected');
  });
});
EOF
```

**Go:**
```bash
# Tests are in same package with _test.go suffix
cat > pkg_test.go <<EOF
package pkg

import "testing"

func TestFunction(t *testing.T) {
    result := Function("input")
    if result != "expected" {
        t.Errorf("got %v, want %v", result, "expected")
    }
}
EOF
```
