# Phase 1: Setup API Foundation - Research
*Generated: 2026-06-20*

## Current State
- The project is an LLM agent for solving hCaptcha.
- It uses `typer` for CLI commands (`hc`).
- `pyproject.toml` contains an optional `server` dependency which originally specified `fastapi`.
- The user has decided to use Flask with Waitress/Gunicorn.

## Technical Findings
- We should replace `fastapi[all]` in `[project.optional-dependencies]` with `flask>=3.0.0`, `waitress>=3.0.0`, `gunicorn>=21.0.0`.
- The server entry point should be integrated into `cli/main.py` using a new `server.py` Typer app.
- Waitress is suitable for Windows production WSGI serving. Gunicorn for Linux. We can do an OS check or just use Waitress by default since it works everywhere.

## Conclusion
We have everything we need to build the API foundation.
