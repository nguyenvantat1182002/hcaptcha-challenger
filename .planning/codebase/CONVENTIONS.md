# Coding Conventions

**Analysis Date:** 2026-04-30

## Naming Patterns

**Files:**
- Python modules use `snake_case.py` (e.g., `src/hcaptcha_challenger/helper/env_generator.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).
- Tests use `test_*.py` naming in `tests/` (e.g., `tests/test_tools_challenge_classifier.py`, `tests/test_schema_image_binary_challenge.py`).
- Packages are organized by domain with nested `__init__.py` exports (e.g., `src/hcaptcha_challenger/tools/__init__.py`, `src/hcaptcha_challenger/tools/spatial/__init__.py`).

**Functions:**
- Functions and methods use `snake_case` (e.g., `normalize_unicode_text`, `create_cache_key`, `test_gemini_point_reasoning`).
- Internal/private helpers are prefixed with `_` (e.g., `_collect_image_files`, `_parse_answer_dict`, `_task_handler`).
- Async tests and tool calls are explicitly prefixed with behavior-focused names (`test_gemini_*`, `process_single_image` in `tests/test_tools_spatial_path_reasoning.py`).

**Variables:**
- Local variables use `snake_case` (e.g., `grid_divisions_path`, `challenge_screenshot`, `expected_type_enum`).
- Module-level constants use `UPPER_SNAKE_CASE` (e.g., `CHALLENGE_CONFIGURATIONS` in `tests/test_tools_challenge_classifier.py`, `DEFAULT_FAST_SHOT_MODEL` in `src/hcaptcha_challenger/models.py`).
- Environment-variable keys are uppercase in settings (`OPENROUTER_API_KEY`, `MOUSE_SPEED` in `src/hcaptcha_challenger/agent/config.py`).

**Types:**
- Pydantic model classes and enums use `PascalCase` (e.g., `CaptchaPayload`, `ImageBinaryChallenge`, `ChallengeTypeEnum` in `src/hcaptcha_challenger/models.py`).
- Type aliases also use `PascalCase`/domain-specific names (e.g., `FastShotModelType`, `IGNORE_REQUEST_TYPE_LITERAL`).
- Literals and unions are heavily used to constrain values in model/config surfaces (`src/hcaptcha_challenger/models.py`, `src/hcaptcha_challenger/agent/config.py`).

## Code Style

**Formatting:**
- Tool used: Black via `pyproject.toml` `[tool.black]`.
- Key settings:
  - `line-length = 100`
  - `target-version = ["py310", "py311", "py312", "py313"]`
  - `skip-string-normalization = true`
  - `exclude = "archive|.venv|docs/.*\\.ipynb"`
- Source files frequently include UTF-8 headers and metadata comment blocks at top of file (`src/hcaptcha_challenger/models.py`, `src/hcaptcha_challenger/utils.py`).

**Linting:**
- Tool used: Ruff via `pyproject.toml` `[tool.ruff]`.
- Key rules:
  - `exclude = ["archive/", "*.ipynb"]`
  - Rule families are not explicitly overridden in `pyproject.toml` (project currently relies on Ruff defaults plus exclusions).

## Import Organization

**Order:**
1. Standard library imports (`json`, `os`, `pathlib`, typing types).
2. Third-party imports (`pydantic`, `loguru`, `dotenv`, `typer`, provider SDKs).
3. Local package imports (`from hcaptcha_challenger...` or relative imports inside package).

**Path Aliases:**
- Not detected (imports use package-qualified absolute imports like `from hcaptcha_challenger.models import ...` and relative imports in provider/tool subpackages).

## Error Handling

**Patterns:**
- Fail-fast validation with explicit exceptions in models/config:
  - `ValueError` raised for invalid settings/rule combinations (`src/hcaptcha_challenger/agent/config.py`, `src/hcaptcha_challenger/models.py`).
- Boundary catch/log/continue pattern around I/O or external calls:
  - `try/except Exception as e` with `logger.error` or `logger.warning` (`src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).
- Retry handling for network-dependent provider calls with `tenacity.retry` (`src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).
- Tests assert explicit error behavior with `pytest.raises(...)` (`tests/test_helper_visualize_attention_points.py`, `tests/test_schema_image_binary_challenge.py`).

## Logging

**Framework:** `loguru` (`src/hcaptcha_challenger/utils.py`)

**Patterns:**
- Centralized logger setup in `init_log()` with stdout and optional file sinks (`src/hcaptcha_challenger/utils.py`).
- Structured level-specific logging in runtime code:
  - `debug` for flow/telemetry
  - `warning` for degraded paths
  - `error` for exception outcomes
  - `success` for task completion (`src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).
- Tests also use logger for diagnostic output in async integration-style tests (`tests/test_tools_spatial_path_reasoning.py`, `tests/test_tools_image_classifier.py`).

## Comments

**When to Comment:**
- Inline comments explain non-obvious behavior, fallbacks, and domain assumptions:
  - Unicode normalization layers (`src/hcaptcha_challenger/models.py`)
  - Retry/model override rationale (`src/hcaptcha_challenger/tools/internal/providers/openrouter.py`)
  - Challenge-flow branches and fallback handling (`src/hcaptcha_challenger/agent/challenger.py`)
- Tests use comments to clarify expected mapping behavior and why assertions target transformed values (`tests/test_schema_image_binary_challenge.py`).

**JSDoc/TSDoc:**
- Not applicable (Python codebase).
- Python docstrings are used consistently for modules, classes, methods, and tests (e.g., `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`, `tests/test_helper_visualize_attention_points.py`).

## Function Design

**Size:** 
- Utility/model methods are usually compact and single-purpose (`src/hcaptcha_challenger/helper/env_generator.py`, `src/hcaptcha_challenger/models.py`).
- Orchestration methods can be long with control-flow branches, especially in agent runtime (`src/hcaptcha_challenger/agent/challenger.py`).

**Parameters:** 
- Prefer explicit keyword args in provider/service APIs (e.g., `generate_with_images(..., *, images, response_schema, ...)` in `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).
- Strong typing with unions/literals for externally configurable values (`src/hcaptcha_challenger/agent/config.py`, `src/hcaptcha_challenger/models.py`).

**Return Values:** 
- Runtime and parsing code returns typed Pydantic models or enum values (`ChallengeRouterResult`, `ChallengeSignal`).
- Utility functions return concrete values/paths (`str`, `Path`, numpy arrays in helper functions used by tests).

## Module Design

**Exports:** 
- Barrel-style package exports are used to present stable public APIs:
  - `src/hcaptcha_challenger/__init__.py`
  - `src/hcaptcha_challenger/tools/__init__.py`
  - `src/hcaptcha_challenger/tools/spatial/__init__.py`
- Internal provider/contracts kept under nested modules (`src/hcaptcha_challenger/tools/internal/providers/`).

**Barrel Files:** 
- Used at package boundaries to simplify imports (`__init__.py` files in `src/hcaptcha_challenger/` and subpackages).
- Recommended project pattern: add new public tool/reasoner exports through nearest package `__init__.py` while keeping implementation in dedicated module files.

---

*Convention analysis: 2026-04-30*
