---
status: complete
---

# Summary

Updated the `CaptchaResponse` instantiation logic where we trigger a manual `SKIP`.
Since the `CaptchaResponse` Pydantic model defines the `is_pass` field with `alias="pass"`, calling `CaptchaResponse(is_pass=True)` ignores the initialization value, leaving it at `False`.
This caused the process to register a `FAILURE` instead of `SUCCESS`.
Replaced it with `CaptchaResponse(**{"pass": True, ...})` to properly assign the field value via its alias.
