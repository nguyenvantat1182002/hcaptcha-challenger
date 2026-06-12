# Phase 3: Tools & Integration Plan

## Objective
Implement sample tools and a headless integration script to verify the OpenRouter Agent's streaming and tool-calling capabilities.

## Context
See `.planning/3-CONTEXT.md` for architectural decisions (Domain-specific tool `click_coordinates`, Automated headless test).

## Steps
1. **Implement `tools.py`**:
   - Create `src/hcaptcha_challenger/tools/internal/providers/openrouter/tools.py`.
   - Define a Pydantic `BaseModel` called `ClickCoordinates` containing `x` (int) and `y` (int).
   - Expose it using OpenAI's `pydantic_function_tool` helper to format it as a valid tool.
2. **Implement `headless.py`**:
   - Create `src/hcaptcha_challenger/tools/internal/providers/openrouter/headless.py`.
   - Set up `asyncio` execution block.
   - Retrieve `OPENROUTER_API_KEY` from the environment or default to a mock string for testing.
   - Initialize `Agent`.
   - Attach the `click_coordinates` tool via `agent.add_tool()`.
   - Register event listeners using decorators (`@agent.on("stream:delta")`, `@agent.on("tool:call")`) to print outputs.
   - Fire a hardcoded prompt: `await agent.send("Please solve the captcha by clicking on the cat. The cat is located at x=120, y=340.")`.

## Verification
- Validate the syntax using Python linters (e.g., `ruff`).
- Run `python src/hcaptcha_challenger/tools/internal/providers/openrouter/headless.py` to ensure events are triggered and the script exits successfully (if API key is provided).
