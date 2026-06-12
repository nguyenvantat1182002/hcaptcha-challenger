# Phase 10 Plan: Supervisor LLM Integration & Guideline Generation

## Context
See `10-CONTEXT.md`. Introduce a Supervisor LLM (`SUPERVISOR_MODEL` from `.env`) to dynamically generate general strategy guidelines based on the challenge prompt and an example image. The guideline will be injected into the `user_prompt` using `## SUPERVISOR GUIDANCE`.

## Execution Steps

1. **Update Configuration**
   - File: `src/hcaptcha_challenger/agent/config.py`
   - Action: Add `SUPERVISOR_MODEL: SCoTModelType = Field(default=DEFAULT_SCOT_MODEL, description="For generating solver guidelines")` to `AgentConfig`.

2. **Create Supervisor Prompt**
   - File: `src/hcaptcha_challenger/tools/supervisor/supervisor.md`
   - Action: Write the markdown system instruction explicitly instructing the AI to output a brief, general strategy for the given prompt and image without hardcoding spatial data.

3. **Create Supervisor Reasoner**
   - File: `src/hcaptcha_challenger/tools/supervisor/agent.py`
   - Action: Implement `SupervisorReasoner` class extending `BaseProvider`. Define `__call__` to accept `challenge_prompt` and `challenge_screenshot` and return a string.
   - File: `src/hcaptcha_challenger/tools/supervisor/__init__.py`
   - Action: Export `SupervisorReasoner`.

4. **Integrate into RoboticArm**
   - File: `src/hcaptcha_challenger/agent/robotic_arm.py`
   - Action: Instantiate `self._supervisor_reasoner = SupervisorReasoner(...)`.
   - Action: Create a stub `_get_or_generate_guideline` method that calls the supervisor directly (caching logic goes to Phase 11).
   - Action: Inject the generated guideline into `user_prompt` for `_image_classifier`, `_spatial_point_reasoner`, and `_spatial_path_reasoner`.

## Verification
- Test using `demo_camoufox.py` and confirm the `SUPERVISOR GUIDANCE` block appears in the logs and accurately guides the model.
