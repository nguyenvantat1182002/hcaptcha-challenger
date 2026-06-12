# Phase 4: Configuration & Provider Abstraction Plan

## Objective
Update the `AgentConfig` class to support multi-provider configuration via API key presence (Gemini vs. OpenRouter), and update the `RoboticArm` initialization to pass the active provider and key downstream to the tools.

## Context
See `.planning/4-CONTEXT.md` for architectural decisions.

## Steps
1. **Modify `AgentConfig` (in `challenger.py`)**:
   - Change `GEMINI_API_KEY` to `SecretStr | None = Field(default=None)`.
   - Add `OPENROUTER_API_KEY: SecretStr | None = Field(default=None)`.
   - Remove the `@field_validator('GEMINI_API_KEY')` block.
   - Add a `@model_validator(mode='after')` to ensure at least one API key is present. If neither is present, raise a `ValueError` with instructions.
   - Add a property `active_provider(self) -> str` that returns `"openrouter"` if `OPENROUTER_API_KEY` is present, otherwise `"gemini"`.
   - Add a property `active_api_key(self) -> str` that returns the secret value of the active provider's key.

2. **Update `RoboticArm` Initialization (in `challenger.py`)**:
   - Update the instantiation of `ChallengeRouter`, `ImageClassifier`, `SpatialPathReasoner`, and `SpatialPointReasoner`.
   - Instead of strictly passing `gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value()`, pass the dynamic values:
     - `provider=self.config.active_provider`
     - `api_key=self.config.active_api_key`
   - *(Note: Changing the Tool classes' `__init__` signatures will actually be handled seamlessly here or in Phase 5, but we will align the parameter names to be generic like `api_key` and `provider`.)*

## Verification
- Validate the syntax using Python linters (e.g., `ruff`).
- Run the core tests if available, or write a quick `assert` test script to ensure `AgentConfig` correctly identifies `active_provider` based on mock `.env` setups.
