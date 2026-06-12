# Phase 8: Dynamic Timeout Configuration

## Objective
To prevent the agent from aborting prematurely when LLM APIs (like OpenRouter) queue or lag heavily (taking anywhere from 10 to 30 minutes). We will expose `LLM_TIMEOUT` to explicitly override the default 10-minute HTTP timeouts enforced by libraries.

## Context
See `.planning/implementation_plan.md` for technical design and scope.

## Steps

### Step 1: Update AgentConfig
- Edit `src/hcaptcha_challenger/agent/config.py`.
- Add `LLM_TIMEOUT: float = Field(default=120.0, description="LLM HTTP timeout in seconds (Set higher if OpenRouter queues)")` to `AgentConfig`.

### Step 2: Update Abstract Tool Layer
- Edit `src/hcaptcha_challenger/tools/internal/base.py`.
- Modify `Reasoner.__init__` to accept `timeout: float | None = None`.
- Modify `_create_default_provider` to pass the `timeout` variable to the instantiated Provider.

### Step 3: Update Concrete Tools
- Edit the `__init__.py` files of all tools to accept and pass `timeout` to `super().__init__`:
  - `src/hcaptcha_challenger/tools/challenge_router/__init__.py`
  - `src/hcaptcha_challenger/tools/image_classifier/__init__.py`
  - `src/hcaptcha_challenger/tools/spatial_path/__init__.py`
  - `src/hcaptcha_challenger/tools/spatial_point/__init__.py`

### Step 4: Update Provider Layer
- Edit `src/hcaptcha_challenger/tools/internal/providers/openrouter/provider.py`.
- Import `httpx`.
- Modify `OpenRouterProvider.__init__` to accept `timeout: float | None = None`.
- Update `AsyncOpenAI` instantiation: if `timeout` is provided, set `timeout=httpx.Timeout(timeout)`. Else use default.

### Step 5: Update RoboticArm Integration
- Edit `src/hcaptcha_challenger/agent/robotic_arm.py`.
- In `__init__`, pass `timeout=self.config.LLM_TIMEOUT` to `ChallengeRouter`, `ImageClassifier`, `SpatialPathReasoner`, and `SpatialPointReasoner`.

### Step 6: Verification
- Create `tests/test_timeout_e2e.py`.
- Write a test instantiating `ImageClassifier` via `OpenRouterProvider` with `timeout=0.01`. Ensure it raises a timeout error (e.g., `httpx.ReadTimeout` or `openai.APITimeoutError`). This proves the timeout flag is correctly passed down the entire stack.
- Run `uv run ruff check`.
