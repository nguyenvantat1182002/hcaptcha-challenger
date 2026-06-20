# Phase 1: Setup API Foundation
*Context gathered on 2026-06-20*

## Domain
Integrate Flask into the project and establish the basic API server skeleton.

## Decisions

### 1. API Structure
- **Decision:** Place the API in a `src/hcaptcha_challenger/server/` module to keep it extensible.
- **Rationale:** Matches the previous FastAPI design and keeps the root clean, making it easier to scale later.

### 2. WSGI Server
- **Decision:** Use `gunicorn` (Linux/Mac) and `waitress` (Windows) for a production-ready setup rather than the development server.
- **Rationale:** The user wants it to be production-ready rather than just using the development server, even if it's an internal API.

## Canonical Refs
- ROADMAP.md - Phase 1 requirements.
- PROJECT.md - Core values and Epic definition.

## Code Context
- The existing structure `src/hcaptcha_challenger/` has models, agents, and utils. We will inject the `server/` package directly alongside them.
- `pyproject.toml` contains an optional `server` dependency block which we will override with Flask, Gunicorn, and Waitress.
