# Phase 11 Plan: Guideline Caching & Invalidation Logic

## Context
See `11-CONTEXT.md`. Introduce a persistent caching mechanism for Supervisor guidelines using a local JSON file (`tmp/.cache/supervisor_guidelines.json`). Track the number of consecutive failures for each challenge type, and invalidate the cached guideline if `fail_count >= SUPERVISOR_INVALIDATION_THRESHOLD`.

## Execution Steps

1. **Update Configuration**
   - File: `src/hcaptcha_challenger/agent/config.py`
   - Action: Add `SUPERVISOR_INVALIDATION_THRESHOLD: int = Field(default=3, description="...")` to `AgentConfig`.

2. **Create Cache Manager**
   - File: `src/hcaptcha_challenger/tools/supervisor/cache.py`
   - Action: Implement `SupervisorCache` to load, save, get, and increment fail counts for prompts in `tmp/.cache/supervisor_guidelines.json`.
   - File: `src/hcaptcha_challenger/tools/supervisor/__init__.py`
   - Action: Export `SupervisorCache`.

3. **Integrate Cache into RoboticArm**
   - File: `src/hcaptcha_challenger/agent/robotic_arm.py`
   - Action: Instantiate `self._supervisor_cache = SupervisorCache(Path(self.config.cache_dir, "supervisor_guidelines.json"), self.config.SUPERVISOR_INVALIDATION_THRESHOLD)`.
   - Action: Initialize `self.last_user_prompt: str | None = None`.
   - Action: Update `challenge_image_*` methods to assign `user_prompt` to `self.last_user_prompt`.
   - Action: Update `_get_or_generate_guideline` to check the cache first. Call the model only on cache miss or invalidation. Catch LLM exceptions.
   - Action: Add `report_challenge_failure` method to increment fail count via `self._supervisor_cache`.

4. **Trigger Invalidation from Challenger**
   - File: `src/hcaptcha_challenger/agent/challenger.py`
   - Action: In `wait_for_challenge`, if the challenge fails (`not cr or not cr.is_pass`), call `self.robotic_arm.report_challenge_failure()`.

## Verification
- Test using a mock script that simulates loading a cache, recording 3 failures, and observing that the 4th call results in the guideline being deleted and regenerated.
