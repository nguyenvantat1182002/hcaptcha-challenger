# Phase 5: Tool Refactoring & Provider Implementation Plan

## Objective
Refactor the internal Tools (`ChallengeRouter`, `ImageClassifier`, `SpatialPathReasoner`, `SpatialPointReasoner`) and their `Reasoner` base class to support multiple providers (Gemini and OpenRouter). Develop an `OpenRouterProvider` that conforms to the `ChatProvider` protocol using OpenRouter's vision models and structured JSON outputs.

## Context
See `.planning/implementation_plan.md` for the technical decisions. User approved the manual JSON Schema injection approach for structured outputs in OpenRouter.

## Steps

### Step 1: Develop `OpenRouterProvider`
- Create `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`.
- Implement `OpenRouterProvider` class adhering to the `ChatProvider` protocol.
- Logic for `generate_with_images`:
  - Convert the local `Path` images to base64 `data:image/jpeg;base64,...` strings.
  - Append the `response_schema.model_json_schema()` to the `description` (system prompt).
  - Use `AsyncOpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")`.
  - Send the request with `response_format={"type": "json_object"}`.
  - Parse the returned JSON text and instantiate `response_schema(**parsed_json)`.

### Step 2: Refactor `Reasoner` Base Class
- File: `src/hcaptcha_challenger/tools/internal/base.py`.
- Update `__init__` signature from `gemini_api_key` to `api_key: str`, and add `provider_type: str = "gemini"`.
- Store `self._provider_type = provider_type`.
- Update `_create_default_provider` to lazily import and instantiate either `GeminiProvider` or `OpenRouterProvider` based on `self._provider_type`.

### Step 3: Refactor Individual Tools
- Update `__init__` signatures in the following files to replace `gemini_api_key` with `api_key` and add `provider`:
  - `src/hcaptcha_challenger/tools/challenge_router/__init__.py`
  - `src/hcaptcha_challenger/tools/image_classifier/__init__.py`
  - `src/hcaptcha_challenger/tools/spatial/path_reasoner.py`
  - `src/hcaptcha_challenger/tools/spatial/point_reasoner.py`
- Pass `api_key=api_key`, `provider_type=provider` to `super().__init__()`.

### Step 4: Verification
- Verify that `uv run ruff check` passes without `TypeError` in the instantiations from Phase 4.
- Perform a headless script test or a mock integration test to guarantee that the `OpenRouterProvider` successfully maps a generic prompt and an image into a structured `Pydantic` response.
