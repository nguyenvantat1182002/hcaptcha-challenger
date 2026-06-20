# Codebase Structure

_Note: The `archive/` directory has been intentionally excluded from this map._

## Root Level
- `src/hcaptcha_challenger/`: Main application code.
- `tests/`: Test suite and end-to-end tests.
- `examples/`: Example scripts and implementations.
- `docker/`: Dockerfiles and container-related configuration.
- `docs/`: Project documentation.
- `pyproject.toml` / `ty.toml` / `uv.lock`: Dependency and build configuration.

## Application Code (`src/hcaptcha_challenger/`)
- `agent/`: Core agent orchestration logic.
- `cli/`: Command-line interface definitions using Typer.
- `helper/`: Helper utilities (e.g., image manipulation, grid creation, visualizers).
- `models.py`: Pydantic data models and schemas.
- `skills/`: Execution behaviors for specific tasks.
- `tools/`: Implementations of various reasoning tools (image classifier, spatial reasoning, etc.).
- `utils.py`: General utility functions.

## Tests (`tests/`)
Contains unit and E2E tests, categorized by functional areas such as visual helpers, reasoning tools, and OpenRouter integration.
