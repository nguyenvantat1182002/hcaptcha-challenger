# Testing Practices

**Date:** 2026-07-16
**Scope:** Core Application

## Frameworks
- `pytest` is the primary test runner.
- `pytest-asyncio` for async tests.

## Configuration
- Test paths are typically `tests/` and `examples/`. (Note: `tests/` directory was intentionally excluded from this codebase map).
- `asyncio_mode = "auto"`
- `asyncio_default_fixture_loop_scope = "function"`

## Coverage / Focus
- Tests generally cover agent capabilities, model execution, and helper functions.
