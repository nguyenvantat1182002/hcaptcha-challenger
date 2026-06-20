---
status: complete
---

# Summary

Updated `AgentV._review_challenge_type` to return `"SKIP"` when it encounters an unknown `request_type` or when an exception occurs during payload parsing. This replaces the previous behavior which defaulted to `await self.robotic_arm.check_challenge_type()` (visual recognition fallback) in those cases. The `_solve_captcha` caller will now receive `"SKIP"` and immediately abort execution for unsupported challenges.
