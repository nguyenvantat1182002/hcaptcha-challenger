# Codebase Concerns

**Analysis Date:** 2025-05-14

## Tech Debt

**Legacy Homoglyph Mapping:**
- Issue: `models.py` contains a `BAD_CODE` dictionary and `normalize_unicode_text` function marked as legacy.
- Files: `src/hcaptcha_challenger/models.py`
- Impact: Clutters the models file and may lead to inconsistent text normalization if newer methods are introduced.
- Fix approach: Move to a dedicated `utils/legacy.py` or replace with a more robust library for Unicode normalization.

**Hardcoded Magic Numbers and Timeouts:**
- Issue: Numerous hardcoded sleep values and timeouts are scattered across the agent logic.
- Files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/agent/robotic.py`
- Impact: Makes the system less adaptable to different network conditions or hardware speeds.
- Fix approach: Centralize all timing and timeout constants into `AgentConfig`.

**Duplicated Coordinate Scaling Logic:**
- Issue: Logic for scaling 0-1000 normalized coordinates to viewport pixels is implemented manually in multiple challenge methods.
- Files: `src/hcaptcha_challenger/agent/robotic.py`
- Impact: High risk of scaling errors and makes it harder to update the coordinate system.
- Fix approach: Create a helper method in `RoboticArm` or a utility class for coordinate transformations.

## Security Considerations

**Token Caching on Disk:**
- Issue: Captcha responses, which may contain sensitive tokens, are saved as JSON files to the local filesystem.
- Files: `src/hcaptcha_challenger/agent/challenger.py` (method `_cache_validated_captcha_response`)
- Impact: If the execution environment is shared or insecure, these tokens could be exfiltrated.
- Current mitigation: Saved to a configurable directory `tmp/.captcha`.
- Recommendations: Disable caching by default or implement a retention policy to auto-delete old responses.

**Environment Secrets Management:**
- Risk: Sensitive API keys for OpenRouter are managed via `.env` files.
- Files: `.env` (observed in root)
- Current mitigation: `.env` is ignored in `.gitignore`.
- Recommendations: Use a proper secrets manager for production deployments and ensure `.env.example` is kept up to date without real keys.

## Performance Bottlenecks

**Synchronous Polling Loop:**
- Problem: `wait_for_challenge` polls for responses with a fixed 1-second sleep.
- Files: `src/hcaptcha_challenger/agent/challenger.py`
- Cause: Simple loop-based waiting for asynchronous browser events.
- Improvement path: Use events or shorter, adaptive polling intervals.

**External LLM Dependency:**
- Problem: Solving challenges requires multiple round-trips to OpenRouter API.
- Files: `src/hcaptcha_challenger/agent/robotic.py`
- Cause: Core architectural design relies on MLLMs for spatial reasoning.
- Improvement path: Implement local model support or caching for similar challenge prompts if applicable.

## Fragile Areas

**DrissionPage Coordinate Bug Workaround:**
- Files: `src/hcaptcha_challenger/agent/robotic.py` (method `screenshot_element_in_frame`)
- Why fragile: Explicitly bypasses library limitations using raw CDP calls. Will break if DrissionPage changes its internal CDP handling or if the bug is fixed/changed.
- Safe modification: Check library updates and use native methods if the coordinate bug is resolved.

**DOM-Based State Detection:**
- Files: `src/hcaptcha_challenger/agent/robotic.py`
- Why fragile: Relies on specific CSS classes (`loading-indicator`, `challenge-view`) and style attributes (`opacity: 0`). hCaptcha frequently updates their DOM to thwart automation.
- Test coverage: Gaps in detecting when the DOM structure has changed, leading to silent failures or timeouts.

**Orphaned Background Threads:**
- Files: `src/hcaptcha_challenger/agent/challenger.py`
- Why fragile: `AgentV` starts a daemon thread in `__init__` that listens to network traffic. There is no `close()` or `stop()` method to clean up this thread or the associated queues.
- Safe modification: Implement a context manager or `shutdown` method for `AgentV`.

## Test Coverage Gaps

**Browser-Heavy Integration Logic:**
- What's not tested: The core `AgentV` and `RoboticArm` logic is tightly coupled with `DrissionPage` and real browser interactions.
- Files: `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/agent/robotic.py`
- Risk: Changes to the core agent logic are difficult to verify without a full browser environment, leading to regressions in edge cases.
- Priority: High

**Error Handling and Fallbacks:**
- What's not tested: Many `suppress(Exception)` blocks and fallback branches (like clicking the first task when no match is found) are not explicitly tested.
- Files: `src/hcaptcha_challenger/agent/robotic.py`
- Risk: Fallback mechanisms might be broken or sub-optimal but remain unnoticed because they are rarely triggered in happy-path tests.
- Priority: Medium

---

*Concerns audit: 2025-05-14*
