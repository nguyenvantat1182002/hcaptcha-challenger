---
slug: fix-pydantic-alias-pass
date: 2026-06-13
---

# Quick Task: Fix CaptchaResponse is_pass initialization

## Goal
Ensure `wait_for_challenge` correctly identifies skipped tasks as SUCCESS by setting the `is_pass` field properly.

## Plan
1. `CaptchaResponse` defines `is_pass` with an alias `"pass"`.
2. Initializing `CaptchaResponse(is_pass=True)` fails to set the field because Pydantic expects the alias name.
3. Fix the initialization to `CaptchaResponse(**{"pass": True, ...})` in `_solve_captcha` and `_task_handler`.
