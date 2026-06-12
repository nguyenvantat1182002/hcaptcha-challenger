# Phase 1: Project Initialization Context

## Decisions

1. **Location**: The OpenRouter Agent core will be implemented in `src/hcaptcha_challenger/tools/internal/providers/openrouter/` (or similar nested structure depending on existing code).
2. **Dependencies**: Dependencies (`openai`, `pyee`) will be added directly to the root `pyproject.toml` of the `hcaptcha-challenger` project.
3. **Environment/Config Management**: API Keys and configurations will be managed using the existing `pydantic-settings` system already present in `hcaptcha-challenger`, rather than using a basic `python-dotenv` setup.

## Next Steps
This context will guide the implementation plan for Phase 1. Downstream agents will use this file to understand the locked architectural choices.
