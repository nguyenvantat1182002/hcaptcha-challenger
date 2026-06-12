# Phase 11 Context: Guideline Caching & Invalidation Logic

## Decisions Made

1. **Cache Location:**
   - Generated guidelines will be stored persistently in the default cache directory at `tmp/.cache/supervisor_guidelines.json`.
   - The file will act as a dictionary keyed by the `challenge_prompt` (e.g., "Find the horse").

2. **Invalidation Threshold:**
   - A new configuration parameter `SUPERVISOR_INVALIDATION_THRESHOLD: int = 3` will be added to `AgentConfig`. This allows users to tweak the `n` consecutive failures via the `.env` file.

3. **Failure Tracking Mechanism (Persistent):**
   - The `fail_count` will be tracked persistently per `challenge_prompt` directly inside `supervisor_guidelines.json`.
   - Data structure example:
     ```json
     {
       "Please click each image containing a cat": {
         "guideline": "Identify dogs by looking for distinct canine features...",
         "fail_count": 0
       }
     }
     ```
   - When the agent fails a challenge (detected after submission), it increments `fail_count` for that prompt.
   - If `fail_count >= SUPERVISOR_INVALIDATION_THRESHOLD`, the cache entry is invalidated, the count is reset, and the Supervisor is invoked again.

## Scope Limits
- Phase 11 covers updating `AgentConfig` for the threshold, creating the caching and invalidation logic inside `RoboticArm` (or a dedicated `SupervisorCache` manager), and incrementing the fail count when `check_challenge_type` detects that the page did not pass.
