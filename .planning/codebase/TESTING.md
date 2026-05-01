# Testing Patterns

**Analysis Date:** 2025-02-14

## Test Framework

**Runner:**
- `pytest`
- Config: `pyproject.toml` (specifically `[tool.pytest.ini_options]`)

**Assertion Library:**
- Standard Python `assert` statements.

**Run Commands:**
```bash
pytest                  # Run all tests
pytest -v               # Verbose mode
pytest tests/test_file.py # Run specific test file
```

## Test File Organization

**Location:**
- Separate directory: `tests/`
- Also includes `examples/` as test paths.

**Naming:**
- `test_*.py` (e.g., `test_tools_challenge_classifier.py`).

**Structure:**
```
tests/
├── challenge_view/     # Test data (images)
├── funcaptcha/         # Tests for FunCaptcha
├── record/             # Record-related tests
├── test_helper_*.py    # Helper utility tests
├── test_tools_*.py      # Tool-specific tests
└── test_schema_*.py    # Schema validation tests
```

## Test Structure

**Suite Organization:**
```python
import pytest
from hcaptcha_challenger import ChallengeClassifier

class TestChallengeClassifier:
    """Challenge classifier test class"""

    @pytest.fixture(scope="class")
    def classifier(self):
        """Create challenge classifier instance"""
        # setup
        yield ChallengeClassifier()
        # teardown

    def test_logic(self, classifier):
        # test logic
        assert classifier is not None
```

**Patterns:**
- **Setup pattern:** Use of `@pytest.fixture` with various scopes (`class`, `function`).
- **Teardown pattern:** `yield` in fixtures for teardown logic.
- **Assertion pattern:** Direct equality checks and boolean assertions.
- **Parametrization:** Heavy use of dynamic test case generation using `pytest.param` and helper functions like `generate_individual_test_cases()`.

## Mocking

**Framework:** `unittest.mock` (standard library) and real API calls for integration tests.

**Patterns:**
- Environment variables are often used to control whether real APIs are called (e.g., `GEMINI_API_KEY`).
- Integration tests in `tests/test_tools_common.py` directly call `google.genai` services.

**What to Mock:**
- Network calls for unit tests.
- File system operations for helper tests (using `Path`).

**What NOT to Mock:**
- Pydantic models and schemas (use real instances).
- Core logic that doesn't have external side effects.

## Fixtures and Factories

**Test Data:**
```python
CHALLENGE_CONFIGURATIONS = [
    {
        "dir_name": "image_drag_drop",
        "expected_map": { ... },
    },
]
```
- Data-driven testing is common, with images stored in `tests/challenge_view/`.

**Location:**
- Test data: `tests/challenge_view/`
- Global fixtures: `conftest.py` (multiple files found in subdirectories).

## Coverage

**Requirements:** None explicitly enforced in `pyproject.toml`.

**View Coverage:**
```bash
pytest --cov=src/hcaptcha_challenger
```
*(Note: `pytest-cov` is not listed in dev dependencies, so this requires manual installation.)*

## Test Types

**Unit Tests:**
- Tests for utilities and helper functions in `test_helper_*.py`.
- Schema validation tests in `test_schema_*.py`.

**Integration Tests:**
- Tests for `ChallengeClassifier` and other tools that may interact with AI models or the file system.
- Examples in `examples/` are also treated as tests.

**E2E Tests:**
- Sentinel and Collector workflows mentioned in `README.md` and `.github/workflows/` suggest E2E or monitoring tests.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_something_async():
    # uses pytest-asyncio
```
- Configured with `asyncio_mode = "auto"` in `pyproject.toml`.

**Error Testing:**
```python
with pytest.raises(SomeException):
    # function call that should fail
```

---

*Testing analysis: 2025-02-14*
