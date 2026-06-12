# Project: hCaptcha Challenger (Core Architecture & Maintenance)

Ensure the core architecture can tolerate extreme latency from LLM APIs (10 to 30 minutes) and support dynamic, supervisor-guided instructions for robust challenge solving over time.

## Current State
**v7 (Planning)**: Milestone 7 initiated. Requirements pending definition.
<details>
<summary>Previous State (v6)</summary>
Milestone 6 completed: Implemented LLM-Guided Instructions with a Supervisor LLM. The supervisor generates guidelines dynamically, caches them securely, and auto-invalidates if `n` consecutive failures occur. Resolved Playwright Firefox HTTP text reading bugs using `APIRequestContext`.
</details>
<details>
<summary>Previous State (v5)</summary>
Milestone 5 completed: Normalized coordinate grid generation and added mapping logic to successfully convert native 0-1000 LLM spatial output back into true viewport coordinates, significantly improving interaction precision.
</details>
<details>
<summary>Previous State (v4)</summary>
Long-Running inference support added via `LLM_TIMEOUT` ensuring resilience against multi-modal models that take up to 30 minutes to respond.
</details>

## Context
With the introduction of OpenRouter, certain complex multi-modal models may queue requests or take up to 30 minutes to yield a response. By default, standard HTTP clients (like `httpx`) and `hcaptcha-challenger`'s internal `EXECUTION_TIMEOUT` will forcibly disconnect the session after 2 to 10 minutes, leading to unhandled `TimeoutError`. We must make `LLM_TIMEOUT` configurable and explicitly override library defaults.

## Architecture
- `src/hcaptcha_challenger/agent/config.py`: For `AgentConfig` and related types.
- `src/hcaptcha_challenger/agent/robotic_arm.py`: For `RoboticArm` and trajectory helpers.
- `src/hcaptcha_challenger/agent/core.py` (or `challenger.py`): For `AgentV` and the main entry point logic.
