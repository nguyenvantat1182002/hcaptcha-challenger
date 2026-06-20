---
slug: toggle-captcha-cache
date: 2026-06-13
---

# Quick Task: Toggle Captcha Cache

## Goal
Add a configuration flag to enable or disable the caching of validated captcha responses.

## Plan
1. Research `config.py` and `challenger.py` to identify where caching occurs.
2. Add `ENABLE_CAPTCHA_CACHE: bool = True` to `AgentConfig` in `config.py`.
3. In `AgentV._cache_validated_captcha_response`, check if `self.config.ENABLE_CAPTCHA_CACHE` is `True` before saving the JSON payload to disk.
