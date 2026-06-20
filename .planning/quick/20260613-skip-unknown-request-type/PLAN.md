---
slug: skip-unknown-request-type
date: 2026-06-13
---

# Quick Task: Skip unknown request_type

## Goal
Modify `AgentV._review_challenge_type` so that if `request_type` is not recognized (or fails to parse), the challenge is immediately skipped rather than falling back to visual recognition.

## Plan
1. Locate `_review_challenge_type` in `src/hcaptcha_challenger/agent/challenger.py`.
2. Find the point after the `match request_type:` block where it logs an unknown request type.
3. Replace the visual fallback return statement with `return "SKIP"` in both the unknown type path and the exception catch block.
