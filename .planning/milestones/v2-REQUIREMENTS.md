# Milestone 2: Multi-Provider Integration Requirements (Archived)

## 1. Multi-Provider Architecture
- [x] Configuration Support (`AgentConfig` must be able to load and validate OpenRouter API keys).
- [x] Abstract Provider Logic (Ensure `ChatProvider` protocol is implemented for OpenRouter).

## 2. Tool Refactoring
- [x] Make `__init__` methods across all `hcaptcha-challenger` tools compatible with dynamic providers (no longer hardcoded to Gemini).
- [x] Handle structured visual outputs in `OpenRouterProvider` (by automatically parsing JSON formats using Pydantic).

## 3. End-to-End Verification
- [x] Validate integration with a real API test connecting `AgentConfig` to `OpenRouterProvider` via the `ImageClassifier`.

## Outcomes
- **Validated**: OpenRouter successfully mimics Gemini's `response_schema` capabilities by utilizing the `json_object` format combined with dynamic schema injection.
- **Adjusted**: Adopted manual schema injection instead of requiring large third-party libraries (like `instructor`).
