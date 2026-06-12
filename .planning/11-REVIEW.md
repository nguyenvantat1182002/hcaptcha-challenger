# Phase 11 Code Review

## Scope
- `src/hcaptcha_challenger/agent/config.py`
- `src/hcaptcha_challenger/agent/robotic_arm.py`
- `src/hcaptcha_challenger/agent/challenger.py`
- `src/hcaptcha_challenger/tools/supervisor/cache.py`

## Findings

### 1. Supervisor Toggle (Enhancement)
- **Finding:** The Supervisor model could not be disabled via configuration. If users want to save tokens or disable the feature globally, they would have to modify the code.
- **Status:** [FIXED] Added `ENABLE_SUPERVISOR` toggle to `AgentConfig` (defaulting to `True`). When disabled, `RoboticArm._get_or_generate_guideline` acts as a no-op, skipping both the caching and the LLM generation layers.

### 2. Cache Key Mapping (Bug)
- **Finding:** The JSON cache was using the massive template string returned by `_match_user_prompt` (or a fallback like "JobType: ...") as the cache key, instead of the actual hCaptcha question (e.g. "Select all objects that have a metal surface"). This caused huge JSON keys and prevented reusing guidelines effectively.
- **Status:** [FIXED] Updated `_match_user_prompt` to intercept the raw `challenge_prompt` before formatting. The cache and the Supervisor LLM prompt now use this short, clean prompt.

### 3. ImageClassifier TypeError (Bug)
- **Finding:** The `challenge_image_label_binary` flow crashed with `TypeError: AsyncCompletions.create() got an unexpected keyword argument 'auxiliary_information'`. This was because `ImageClassifier.__call__` did not explicitly accept `auxiliary_information`, so it was mistakenly forwarded directly to the OpenRouter client library as a raw kwarg.
- **Status:** [FIXED] Updated `ImageClassifier.__call__` to explicitly accept `auxiliary_information` and properly append it to `user_prompt` before delegating to `_provider.generate_with_images`.

### 4. Fetch Execution Bug (Bug)
- **Finding:** The `fetch` fallback added to bypass `NS_ERROR_INVALID_CONTENT_ENCODING` was declaring an `async () => {}` function inside `page.evaluate()` but missing the `()` to invoke it (IIFE). This caused the script to evaluate to a function object silently instead of actually running, leading to `hsw.js` never being executed and the challenge timing out. However, fixing the IIFE revealed that making a second request from within the browser context using `fetch(response.url)` can cause context crashes due to session/token mismatches.
- **Status:** [FIXED] Abandoned `fetch()` and `response.text()` entirely. Updated `_task_handler` to use Playwright's `APIRequestContext` (`self.page.request.get(response.url)`) which reliably downloads the `hsw.js` script and decodes it without encountering the Firefox network stack bugs.

### 5. Failure Reporting Circuit (Info)
- **Finding:** The failure reporting circuit (`report_challenge_failure`) correctly integrates into `challenger.py`'s `wait_for_challenge` lifecycle block. 
- **Recommendation:** No further action required. The threshold trigger is robust.

## Summary
Phase 11's caching functionality is robust. The code has been successfully updated during review to allow dynamic enabling/disabling of the entire Supervisor integration subsystem via the `ENABLE_SUPERVISOR` configuration flag.
