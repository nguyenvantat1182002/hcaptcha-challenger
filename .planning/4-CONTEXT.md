# Phase 4: Configuration Context

## Decisions

1. **Auto-detect Provider by API Key**: Per user request, the system will automatically detect the provider based on the provided API key.
   - If `OPENROUTER_API_KEY` is set in `.env` -> Use OpenRouter.
   - If `GEMINI_API_KEY` is set in `.env` -> Use Gemini.
   - If both are set, we will prioritize OpenRouter (or we can add a fallback priority).
2. **Validator Adjustment**: Instead of failing if `GEMINI_API_KEY` is missing, the `AgentConfig` will use a root validator (`@model_validator(mode='after')`) to verify that *at least one* API key is provided.

## Next Steps
This simplifies the configuration significantly. No explicit `AI_PROVIDER` string is strictly required for the user to set, though we will maintain an internal property `active_provider` to cleanly route logic.
