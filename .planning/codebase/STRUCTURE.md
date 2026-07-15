# Directory Structure

**Date:** 2026-07-16
**Scope:** Core Application

## Excluded from Map
- `.vscode/`, `.github/`, `archive/`, `docker/`, `docs/`, `tests/`

## Layout
- `pyproject.toml` - Project configuration and dependencies.
- `src/hcaptcha_challenger/` - Main source code package.
  - `agent/` - Agent logic for browser interaction and challenge management.
  - `cli/` - Command Line Interface implementation (using Typer).
  - `helper/` - Auxiliary scripts and logic.
  - `server/` - Flask API wrapper for exposing the solver.
  - `skills/` - Specialized challenge solving capabilities.
  - `tools/` - General utility functions.
  - `models.py` - Core data models (Pydantic/Dataclasses).
  - `utils.py` - Common utilities.
- `examples/` - Example scripts demonstrating how to use the library.
