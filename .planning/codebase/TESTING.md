# Testing

## Framework
- **Primary Framework**: `pytest`
- **Async Support**: `pytest-asyncio` with `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "function"`.
- **Warnings**: Deprecation warnings are configured to be ignored during test runs.

## Test Areas
- **Tools**: Validation of reasoning tools (spatial bbox, path, point) and classifiers (image, challenge).
- **Helpers**: Validation of image manipulation functions (grid creation, comparison image) and environment generators.
- **Schemas**: Testing Pydantic validation for challenge schemas.

## Continuous Integration
Automated testing is integrated into GitHub Actions:
- **python-pytest.yaml**: Runs the test suite on relevant pull requests and commits.
- Test paths explicitly encompass both `tests/` and `examples/`.

*(Note: The `archive` component has been explicitly excluded from this map.)*
