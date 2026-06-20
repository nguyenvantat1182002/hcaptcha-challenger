---
status: complete
---

# Summary

Added the `ENABLE_CAPTCHA_CACHE` flag to `AgentConfig`. 
Modified `AgentV._cache_validated_captcha_response` to verify this flag before writing JSON output to disk. If `ENABLE_CAPTCHA_CACHE` is `False`, the response is still appended to `cr_list` for local state tracking, but the filesystem operation is skipped.
