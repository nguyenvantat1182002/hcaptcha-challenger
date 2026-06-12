# Milestone 4: Long-Running Inference Support Requirements (Archived)

## 1. Dynamic Timeout Configuration
- [x] Add `LLM_TIMEOUT: float` to `AgentConfig` in `src/hcaptcha_challenger/agent/config.py` (default: 120.0 seconds).
- [x] Update `EXECUTION_TIMEOUT` or add documentation to ensure users know that if `LLM_TIMEOUT` is high, `EXECUTION_TIMEOUT` must also be scaled proportionally.

## 2. HTTP Client Timeout Adjustments
- [x] Update `OpenRouterProvider` in `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py` to accept the `timeout` parameter and pass it to `AsyncOpenAI` via `httpx.Timeout`.
- [x] Ensure that `timeout` explicitly overrides the default 10-minute (600s) timeout of `httpx` so requests can survive up to 30 minutes (1800s) if configured.
- [x] Update `GeminiProvider` in `src/hcaptcha_challenger/tools/internal/providers/gemini.py` to accept and pass the timeout to `google.genai.Client` via `http_options`.

## 3. Tool Refactoring
- [x] Update `Reasoner`, `ImageClassifier`, `ChallengeRouter`, `SpatialPathReasoner`, and `SpatialPointReasoner` to accept an optional `timeout` argument and forward it to their respective underlying Providers.

## 4. Verification
- [x] Validate the timeout behavior by injecting an artificially low timeout (e.g., `0.01s`) in a test to ensure the Timeout exception is triggered, proving the parameter is wired correctly for both providers.
