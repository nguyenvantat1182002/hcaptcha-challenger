# Testing

## Frameworks
- **Primary Framework**: `pytest`
- **Asynchronous Testing**: `pytest-asyncio`

## Test Approach
- **Unit Tests**: Found in `tests/`, covering helper functions, Pydantic schemas, and tool modules (e.g., bounding box, path reasoning).
- **End-to-End (E2E) Tests**: Contains tests simulating real integrations (e.g., `test_openrouter_e2e.py`, `test_timeout_e2e.py`) to ensure the agent orchestrates the entire challenge flow correctly.

## Configuration
- `pytest.ini_options` in `pyproject.toml` sets test paths to `["tests", "examples"]` and configures `asyncio_mode = "auto"`.
