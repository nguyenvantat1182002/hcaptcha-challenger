---
status: complete
---

# Summary

Added logic to `_solve_captcha` to push a `CaptchaResponse` with `error="skipped_by_unknown_type"` into `_captcha_response_queue` if the challenge type resolves to `"SKIP"` and the queue is empty. This prevents `wait_for_challenge` from waiting indefinitely (up to 30s) when a challenge is aborted due to an unknown `request_type`.
