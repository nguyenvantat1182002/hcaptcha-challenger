# Testing Patterns

**Analysis Date:** 2026-04-30

## Test Framework

**Runner:**
- `pytest` (declared in dev dependencies in `pyproject.toml`; executed in `.github/workflows/python-pytest.yaml`).
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`.

**Assertion Library:**
- Built-in `pytest` assertions (`assert ...`, `pytest.raises(...)` in `tests/test_schema_image_binary_challenge.py` and `tests/test_helper_visualize_attention_points.py`).

**Run Commands:**
```bash
pytest                             # Run all tests
pytest tests                       # Run primary test suite directory
pytest tests -k "spatial"          # Run targeted subset by keyword
```

## Test File Organization

**Location:**
- Main tests are in top-level `tests/`.
- Additional executable examples also participate in pytest discovery due to `testpaths = ["tests", "examples"]` in `pyproject.toml`.

**Naming:**
- Test files follow `test_*.py` (e.g., `tests/test_tools_spatial_point_reasoning.py`, `tests/test_helper_env_generator.py`).

**Structure:**
```
tests/
  test_helper_*.py
  test_schema_*.py
  test_tools_*.py
  challenge_view/          # fixture/input image assets used by tool tests
  show_answer/             # generated output artifacts from some tests
```

## Test Structure

**Suite Organization:**
```typescript
class TestChallengeClassifier:
    @pytest.fixture(scope="class")
    def classifier(self): ...

    @pytest.mark.parametrize("image_file, expected_type_enum", generate_individual_test_cases())
    async def test_challenge_classifier(...): ...
```

**Patterns:**
- Setup pattern:
  - Module-level env setup with `dotenv.load_dotenv()` for API-backed tests (`tests/test_tools_image_classifier.py`, `tests/test_tools_challenge_classifier.py`).
  - `@pytest.fixture` for reusable objects/images/bounding boxes (`tests/test_helper_visualize_attention_points.py`).
- Teardown pattern:
  - `try/finally` cleanup for temporary files (`tests/test_helper_visualize_attention_points.py`).
  - Minimal explicit teardown; relies on fixture scope and filesystem cleanup guards.
- Assertion pattern:
  - Type assertions before behavior assertions (`assert isinstance(...)` then field/value checks).
  - Parametrized expected-value matching for model normalization/mapping logic (`tests/test_schema_image_binary_challenge.py`).

## Mocking

**Framework:** `unittest.mock.patch` decorators/context managers inside pytest suites.

**Patterns:**
```typescript
@patch('matplotlib.pyplot.show')
@patch('matplotlib.pyplot.savefig')
def test_show_answer_points_save(...):
    ...
    mock_savefig.assert_called_once()
```

**What to Mock:**
- UI/plot side effects (`matplotlib.pyplot.show`, `matplotlib.pyplot.savefig`) in visualization tests (`tests/test_helper_visualize_attention_points.py`).
- Expensive display interactions while preserving image-processing logic.

**What NOT to Mock:**
- Core data/model transformations (`BoundingBoxCoordinate`, `ImageBinaryChallenge` logic in `tests/test_schema_image_binary_challenge.py`).
- Most integration-style tool invocations are not mocked and rely on real API keys/data (`tests/test_tools_*` files).

## Fixtures and Factories

**Test Data:**
```typescript
@pytest.fixture
def area_select_answer():
    return ImageAreaSelectChallenge(
        challenge_prompt="Select all images with traffic lights",
        points=[PointCoordinate(x=100, y=100), ...],
    )
```

**Location:**
- Inline fixtures live within each test module (no shared `tests/conftest.py` detected).
- Static image datasets are under `tests/challenge_view/` and discovered via helper functions like `_collect_image_files(...)`.

## Coverage

**Requirements:** None enforced (no `pytest-cov` config, no coverage threshold in `pyproject.toml` or workflow config).

**View Coverage:**
```bash
Not detected
```

## Test Types

**Unit Tests:**
- Schema/model and helper behavior checks with deterministic inputs and direct assertions (`tests/test_schema_image_binary_challenge.py`, `tests/test_helper_create_coordinate_grid.py`).

**Integration Tests:**
- API/model integration tests that invoke Gemini/OpenRouter-backed tool classes with real env keys and image assets (`tests/test_tools_image_classifier.py`, `tests/test_tools_spatial_*_reasoning.py`, `tests/test_tools_challenge_classifier.py`).

**E2E Tests:**
- Not used as a separate framework (no Playwright/Cypress/Pytest-Playwright E2E suite detected in active `tests/` package).

## Common Patterns

**Async Testing:**
```typescript
@pytest.mark.parametrize("challenge_screenshot", _collect_image_files())
async def test_gemini_path_reasoning(challenge_screenshot: Path):
    results = await spr(challenge_screenshot=challenge_screenshot, grid_divisions=grid_divisions_path)
    assert results.log_message
```

**Error Testing:**
```typescript
with pytest.raises(ValueError):
    _parse_answer_dict(invalid_dict)
```

---

*Testing analysis: 2026-04-30*
