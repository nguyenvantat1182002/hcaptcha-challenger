# Phase 1: Setup API Foundation - Plan
*Generated: 2026-06-20*

## Goals
Integrate Flask into the project and establish the basic API server skeleton.

## Tasks
1. **Update Dependencies:** In `pyproject.toml`, replace `fastapi[all]` in `[project.optional-dependencies]` with `flask>=3.0.0`, `waitress>=3.0.0`, `gunicorn>=21.0.0`.
2. **Create Core Server Module:** Create `src/hcaptcha_challenger/server/app.py` with a basic Flask app and `/health` route.
3. **Create CLI Command:** Create `src/hcaptcha_challenger/cli/server.py` and register it in `cli/main.py`.

## Risks
- None expected. This is purely setup.
