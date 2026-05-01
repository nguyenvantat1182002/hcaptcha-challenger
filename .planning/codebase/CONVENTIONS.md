# Coding Conventions

**Analysis Date:** 2025-02-14

## Naming Patterns

**Files:**
- `snake_case.py` (e.g., `models.py`, `utils.py`, `main.py`).

**Functions:**
- `snake_case` (e.g., `normalize_unicode_text`, `init_log`).

**Variables:**
- `snake_case` (e.g., `result`, `bad_char`, `log_level`).

**Types:**
- Classes: `PascalCase` (e.g., `ChallengeSignal`, `BaseModel`, `SiteKey`).
- Type Aliases: `PascalCase` (e.g., `FastShotModelType`, `SCoTModelType`).

**Constants and Enums:**
- `UPPER_CASE` (e.g., `BAD_CODE`, `SUCCESS`, `DEFAULT_FAST_SHOT_MODEL`).

## Code Style

**Formatting:**
- `black` is used for code formatting.
- Key settings: `line-length = 100`, `skip-string-normalization = true`.
- Target versions: `py310`, `py311`, `py312`, `py313`.

**Linting:**
- `ruff` is used for linting.
- Configuration is present in `pyproject.toml`.
- Excludes: `archive/`, `*.ipynb`.

## Import Organization

**Order:**
1. Future imports (`from __future__ import annotations`).
2. Standard library imports (e.g., `import os`, `import json`).
3. Third-party library imports (e.g., `import pytest`, `from pydantic import BaseModel`).
4. Local project imports (e.g., `from hcaptcha_challenger import models`).

**Path Aliases:**
- Not detected. Standard relative and absolute imports within `src/hcaptcha_challenger`.

## Error Handling

**Patterns:**
- Extensive use of Pydantic for data validation and schema enforcement.
- Custom signals and enums for challenge status (`ChallengeSignal`).
- Standard Python exceptions for control flow (e.g., `raise typer.Exit()`).

## Logging

**Framework:** `loguru`

**Patterns:**
- Custom initialization in `src/hcaptcha_challenger/utils.py` via `init_log()`.
- Pre-configured sinks for `runtime`, `error`, and `serialize`.
- Specialized formatters with colorization and Shanghai timezone.
- Logs are typically initialized in `src/hcaptcha_challenger/__init__.py`.

## Comments

**When to Comment:**
- To explain complex logic (e.g., Unicode normalization layers in `models.py`).
- Legacy code references.
- TODOs (though few were seen in primary files).

**JSDoc/TSDoc:**
- Google Style docstrings are used for functions and classes.
- Includes `Args`, `Returns`, and `Parameter` (in some cases) sections.

## Function Design

**Size:**
- Functions are generally concise and focused on a single responsibility.
- Large logic blocks are broken into "layers" or sub-functions.

**Parameters:**
- Uses type hints for all parameters.
- Mix of positional and keyword arguments.
- Use of `**sink_channel` or similar for flexible configuration.

**Return Values:**
- Uses type hints for return values.
- Often returns Pydantic models or Enums for structured data.

## Module Design

**Exports:**
- Uses `__all__` in `__init__.py` files to explicitly define public API (e.g., `src/hcaptcha_challenger/__init__.py`).

**Barrel Files:**
- `__init__.py` acts as a barrel file to expose core functionality from sub-packages (`agent`, `tools`, `models`).

---

*Convention analysis: 2025-02-14*
