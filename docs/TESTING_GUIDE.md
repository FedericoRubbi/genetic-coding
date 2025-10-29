# Testing Guide

## 🎯 Overview

This project uses **pytest** for all testing - both unit tests and integration tests. This provides a professional, structured approach similar to Jest in JavaScript.

## 📁 Test Structure

```
tests/
├── conftest.py                    # Pytest configuration & fixtures
├── pytest.ini                     # Pytest settings
│
├── test_genome.py                 # ✅ Unit tests (genome structure)
├── test_codegen.py                # ✅ Unit tests (code generation)
│
├── test_supercollider_pytest.py   # 🎵 Integration tests (SC server)
├── test_superdirt_pytest.py       # 🎵 Integration tests (SuperDirt)
├── test_tidalcycles_pytest.py     # 🎵 Integration tests (Tidal patterns)
│
└── test_*.py (old scripts)        # ⚠️  Legacy manual tests
```

## 🚀 Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-cov pytest-xdist
```

### Run All Tests

```bash
pytest
```

### Run Only Unit Tests (No External Dependencies)

```bash
pytest -m unit
```

### Run Integration Tests

```bash
pytest -m integration
```

## 🎯 Test Markers

We use pytest markers to organize tests:

| Marker | Description | External Deps |
|--------|-------------|---------------|
| `unit` | Unit tests | None |
| `integration` | Integration tests | Varies |
| `supercollider` | Requires SC server | SuperCollider |
| `superdirt` | Requires SuperDirt | SC + SuperDirt |
| `audio` | Produces audio | SC + SuperDirt |
| `slow` | Slow-running tests | None |

### Examples

```bash
# Run only SuperCollider tests
pytest -m supercollider

# Run tests that DON'T require audio
pytest -m "not audio"

# Run unit tests and non-audio integration tests
pytest -m "unit or (integration and not audio)"

# Run specific test file
pytest tests/test_genome.py -v

# Run specific test class
pytest tests/test_superdirt_pytest.py::TestSuperDirtBasics -v

# Run specific test
pytest tests/test_genome.py::test_pattern_tree_creation -v
```

## 🔧 Fixtures

Pytest fixtures provide reusable test setup. Defined in `conftest.py`:

### `supercollider_client`
OSC client for SuperCollider server (port 57110)
```python
def test_my_sc_feature(supercollider_client):
    supercollider_client.send_message("/status", [])
```

### `superdirt_client`
OSC client for SuperDirt (port 57120)
```python
def test_my_dirt_feature(superdirt_client):
    superdirt_client.send_message("/dirt/play", [...])
```

### `backend`
Backend instance with cleanup
```python
def test_backend_feature(backend):
    backend.send_pattern('sound "bd"')
```

## 📊 Test Organization

### Unit Tests (Pytest Style)

```python
# tests/test_genome.py
import pytest
from genetic_music.genome import PatternTree

def test_pattern_tree_creation():
    """Test pattern tree generation."""
    tree = PatternTree.random(max_depth=3)
    assert tree is not None
    assert tree.depth() <= 3

@pytest.mark.parametrize("depth", [1, 2, 3, 4, 5])
def test_different_depths(depth):
    """Test trees at different depths."""
    tree = PatternTree.random(max_depth=depth)
    assert tree.depth() <= depth
```

### Integration Tests (Pytest Style)

```python
# tests/test_superdirt_pytest.py
import pytest

@pytest.mark.superdirt
@pytest.mark.integration
@pytest.mark.audio
class TestSuperDirtBasics:
    """SuperDirt functionality tests."""
    
    def test_kick_drum(self, superdirt_client):
        """Test playing a kick drum."""
        superdirt_client.send_message("/dirt/play", [
            "s", "bd", "orbit", 8, "gain", 1.0
        ])
        assert True
    
    @pytest.mark.parametrize("sample", ["bd", "sn", "hh"])
    def test_samples(self, superdirt_client, sample):
        """Test different samples."""
        superdirt_client.send_message("/dirt/play", [
            "s", sample, "orbit", 8
        ])
        assert True
```

## 🎨 Advanced Features

### Parametrized Tests

Test multiple inputs without writing duplicate code:

```python
@pytest.mark.parametrize("sample,gain", [
    ("bd", 1.0),
    ("sn", 0.8),
    ("hh", 0.6),
])
def test_samples_with_gain(superdirt_client, sample, gain):
    superdirt_client.send_message("/dirt/play", [
        "s", sample, "gain", gain
    ])
```

### Test Classes

Group related tests:

```python
class TestPatternGeneration:
    """Group pattern generation tests."""
    
    def test_simple_pattern(self):
        ...
    
    def test_complex_pattern(self):
        ...
```

### Skip Tests Conditionally

```python
@pytest.mark.skipif(not is_supercollider_available(),
                    reason="SuperCollider not running")
def test_requires_sc(supercollider_client):
    ...
```

### Expected Failures

```python
@pytest.mark.xfail(reason="Known issue #123")
def test_buggy_feature():
    ...
```

## 📈 Coverage Reports

Generate code coverage reports:

```bash
# Generate coverage report
pytest --cov=src/genetic_music --cov-report=html

# View report
open htmlcov/index.html
```

## 🔄 Continuous Integration

The pytest structure makes CI/CD easy:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest -m unit  # Only unit tests in CI
```

## 📝 Best Practices

### ✅ DO

- **Use fixtures** for shared setup
- **Use markers** to categorize tests
- **Use parametrize** for multiple test cases
- **Keep tests isolated** (no shared state)
- **Name tests clearly** (test_<what>_<condition>)
- **Write docstrings** explaining what's tested

### ❌ DON'T

- Don't use `input()` or interactive prompts
- Don't use `print()` for assertions (use `assert`)
- Don't share state between tests
- Don't test multiple things in one test
- Don't skip writing tests for edge cases

## 🆚 Comparison: Old vs New

### Old Approach (Scripts)

```python
# test_supercollider.py
if __name__ == "__main__":
    print("Prerequisites:")
    print("  1. Start SuperCollider")
    input("Press Enter...")
    
    client = SimpleUDPClient("127.0.0.1", 57110)
    print("Test 1: Status")
    client.send_message("/status", [])
    print("✓ Passed")
```

**Problems:**
- ❌ Manual interaction required
- ❌ No automatic discovery
- ❌ Hard to run in CI/CD
- ❌ No fixtures/reuse
- ❌ Can't selectively run tests

### New Approach (Pytest)

```python
# test_supercollider_pytest.py
@pytest.mark.supercollider
def test_status_request(supercollider_client):
    """Test server status request."""
    supercollider_client.send_message("/status", [])
    assert True
```

**Benefits:**
- ✅ Automatic discovery
- ✅ Runs in CI/CD
- ✅ Uses fixtures
- ✅ Selective execution
- ✅ Parametrization
- ✅ Better reporting

## 🎯 Common Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific marker
pytest -m unit
pytest -m "integration and not audio"

# Run specific file
pytest tests/test_genome.py

# Run specific test
pytest tests/test_genome.py::test_pattern_tree_creation

# Run tests in parallel (faster)
pytest -n auto

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show slowest tests
pytest --durations=10

# Generate coverage
pytest --cov=src/genetic_music

# Run with coverage and HTML report
pytest --cov=src/genetic_music --cov-report=html
```

## 🔍 Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger immediately
pytest --trace

# Verbose traceback
pytest --tb=long

# Short traceback
pytest --tb=short

# No traceback capture
pytest --tb=native
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)

## 🎉 Summary

The new pytest-based structure provides:

✅ **Professional testing framework** (like Jest for JavaScript)  
✅ **Automatic test discovery**  
✅ **Fixtures for reusable setup**  
✅ **Markers for test organization**  
✅ **Parametrization for multiple test cases**  
✅ **CI/CD ready**  
✅ **Coverage reports**  
✅ **Better developer experience**  

Run `pytest -v` to see the improved testing structure in action!

