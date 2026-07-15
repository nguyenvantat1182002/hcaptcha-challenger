# Coding Conventions

**Date:** 2026-07-16
**Scope:** Core Application

## Style
- Python code is formatted with `black` (line-length = 100).
- Linting is enforced by `ruff`.
- Uses type hinting extensively for clarity (Python >=3.10 required).

## Architecture Conventions
- **Pydantic**: Used for settings management and data validation (`pydantic-settings`).
- **Logging**: Uses `loguru` for robust and colored logging outputs instead of standard logging.
- **CLI**: Commands are structured using `typer`.
- **Async**: Employs `asyncio` for concurrent operations, especially with browser automation via Playwright.

## File Naming
- Python files use `snake_case`.
