---
slug: handle-skip-queue-hang
date: 2026-06-13
---

# Quick Task: Fix queue hanging on SKIP

## Goal
Fix `wait_for_challenge` getting stuck when `_review_challenge_type` returns `"SKIP"` due to unknown `request_type`.

## Plan
1. Update `_solve_captcha` in `challenger.py`.
2. When `challenge_type == "SKIP"`, check if `_captcha_response_queue` is empty.
3. If it is empty, push a dummy `CaptchaResponse` (e.g. `is_pass=True`) into the queue so that `wait_for_challenge` can unblock immediately instead of timing out.
