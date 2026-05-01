# Coding Conventions

**Analysis Date:** 2025-05-14

## Naming Patterns

**Files:**
- Use `snake_case` for all Python files (e.g., `models.py`, `utils.py`).

**Functions:**
- Use `snake_case` for function and method names (e.g., `normalize_unicode_text`, `init_log`).

**Variables:**
- Use `snake_case` for variables and parameters (e.g., `sink_channel`, `log_level`).

**Types:**
- Use `PascalCase` for class names (e.g., `ChallengeSignal`, `ImageClassifier`, `SiteKey`).
- Use `UPPER_CASE` for `Enum` members (e.g., `SUCCESS`, `FAILURE`).

## Code Style

**Formatting:**
- **Tool:** `black`
- **Key settings:** 
  - Line length: 100 characters.
  - Skip string normalization: `true` (prefer keeping user's choice of quotes).
  - Target versions: Python 3.10+.

**Linting:**
- **Tool:** `ruff`
- **Key rules:** Default ruff rules are applied, excluding `archive/` and Jupyter notebooks.

## Import Organization

**Order:**
- Standard library imports first.
- Third-party library imports second.
- Local project imports third.
- Grouped and sorted alphabetically within each group (managed by `ruff`).

**Path Aliases:**
- None detected; standard relative and absolute imports used (e.g., `from hcaptcha_challenger import ImageClassifier`).

## Error Handling

**Patterns:**
- Extensive use of `Pydantic` for data validation and schema enforcement.
- Custom signals and status enums for flow control (e.g., `ChallengeSignal`).

## Logging

**Framework:** `loguru`

**Patterns:**
- Centralized log initialization in `src/hcaptcha_challenger/utils.py` via `init_log()`.
- Use of descriptive log levels (`DEBUG`, `INFO`, `TRACE`, `ERROR`).
- Custom formatting with colors and timestamps.
- Contextual logging with `{extra}` fields.

## Comments

**When to Comment:**
- File headers are mandatory, including encoding, date, author, GitHub link, and description.
- Complexity-heavy functions (e.g., `normalize_unicode_text`) include step-by-step logic explanations.

**JSDoc/TSDoc:**
- Google/Numpy style docstrings using triple double quotes `"""`.
- Includes "Args", "Returns", and "Parameter" sections.

## Function Design

**Size:** Generally focused and modular.

**Parameters:** Use of keyword-only arguments or `**kwargs` for flexibility in configuration (e.g., `init_log`).

**Return Values:** Explicit type hinting for return values, often using `Union` or `Optional`.

## Module Design

**Exports:** Controlled via `__init__.py` files to expose public API (e.g., `src/hcaptcha_challenger/__init__.py`).

**Barrel Files:** `__init__.py` used to simplify imports for users.

---

*Convention analysis: 2025-05-14*
