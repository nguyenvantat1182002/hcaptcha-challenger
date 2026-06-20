# Conventions

## Coding Standards
- **Formatting & Linting**: Enforced via `black` (line length 100) and `ruff`.
- **Type Hinting**: Extensive use of Python type hints, validated via Pydantic models where appropriate.
- **Asynchronous Programming**: Uses `asyncio` for non-blocking I/O operations (HTTP requests, Playwright interactions).

## Error Handling & Logging
- **Logging**: Uses `loguru` for structured, leveled logging.

## Dependency Management
- **Packaging**: Uses `pyproject.toml` with `hatchling` and `uv-dynamic-versioning`. Optional dependency groups (`server`, `dataset`, `camoufox`) keep the core lightweight.
