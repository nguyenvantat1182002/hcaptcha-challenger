# Testing Patterns

**Analysis Date:** 2025-05-14

## Test Framework

**Runner:**
- `pytest`
- Config: `pyproject.toml` ([tool.pytest.ini_options])

**Assertion Library:**
- Standard `assert` statements.

**Run Commands:**
```bash
pytest                 # Run all tests
pytest -v              # Verbose mode
pytest tests/test_*.py # Run specific test suite
```

## Test File Organization

**Location:**
- Separate directory: `tests/`
- Also includes `examples/` as test paths.

**Naming:**
- Files: `test_*.py`
- Functions: `test_*`

**Structure:**
```
tests/
├── challenge_view/    # Test fixtures (images, etc.)
├── record/           # Multimedia test data
├── test_tools_*.py   # Tool-specific integration tests
└── test_helper_*.py  # Helper utility tests
```

## Test Structure

**Suite Organization:**
```python
import pytest
from hcaptcha_challenger import ImageClassifier

# Fixtures or globals
ic = ImageClassifier(...)

@pytest.mark.parametrize("input, expected", [...])
async def test_feature(input):
    results = await ic(input)
    assert results is not None
```

**Patterns:**
- **Parametrization:** Frequent use of `@pytest.mark.parametrize` to run same test logic against multiple local files.
- **Async Testing:** Extensive use of `async def` with `pytest-asyncio` for I/O bound operations (API calls).
- **Visualization:** Many tests generate "answer" visualizations in `tests/show_answer/` to verify spatial reasoning visually.

## Mocking

**Framework:** None prominently used; tests favor real integration.

**Patterns:**
- Real API keys are loaded via `python-dotenv`.
- Tests interact directly with LLM providers (Gemini) to verify solver accuracy.

**What to Mock:**
- Not strictly enforced; current strategy prioritizes integration over unit isolation for core solver logic.

## Fixtures and Factories

**Test Data:**
- Local image/video files stored in `tests/challenge_view/` and `tests/record/`.
- Dynamic coordinate grids created during test execution.

**Location:**
- `tests/challenge_view/`

## Coverage

**Requirements:** None enforced in `pyproject.toml`.

**View Coverage:**
```bash
pytest --cov=src/hcaptcha_challenger
```

## Test Types

**Unit Tests:**
- Used for utility functions in `test_helper_*.py`.

**Integration Tests:**
- Primary test type. Verifies `ImageClassifier`, `SpatialPointReasoner`, etc., against real challenge screenshots.

**E2E Tests:**
- Playwright-based tests (e.g., `tests/test_normal_playwright.py`) verify the full browser interaction flow.

## Common Patterns

**Async Testing:**
- Use `asyncio.gather` for concurrent processing of multiple test cases within a single test function.

**Error Testing:**
- Validating `ChallengeSignal` responses for edge cases.

---

*Testing analysis: 2025-05-14*
