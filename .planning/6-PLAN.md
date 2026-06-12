# Phase 6: E2E Testing & Verification Plan

## Objective
Verify that the `hcaptcha-challenger` Multi-Provider architecture operates seamlessly from configuration through down to the OpenRouter LLM using structured JSON outputs, specifically for visual tasks.

## Context
See `.planning/implementation_plan.md` for technical decisions. The user approved executing a live OpenRouter API call.

## Steps

### Step 1: Create Test Script
- Create file: `tests/test_openrouter_e2e.py`.
- Write an `async` test function using `pytest.mark.asyncio`.
- Initialize `AgentConfig` dynamically (it will auto-detect the `OPENROUTER_API_KEY` from `.env`).
- Skip the test dynamically if `OPENROUTER_API_KEY` is not present to prevent CI/CD failures on environments without the key.
- Initialize `ImageClassifier` with `api_key=config.active_api_key` and `provider=config.active_provider`.
- Locate the test image at `tests/challenge_view/image_label_binary/1.png` (or another valid mock image).
- Execute the classifier's `__call__` method on the image.
- Assert that the returned object is an instance of `ImageBinaryChallenge`.
- Assert that the `target` list inside the challenge is properly structured (e.g., contains valid boolean coordinates).

### Step 2: Verification
- Execute `uv run pytest tests/test_openrouter_e2e.py -v -s`.
- If the test passes, the multi-provider system is successfully validated and Milestone 2 is officially complete!
