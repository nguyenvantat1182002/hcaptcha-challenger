# Integrations

**Date:** 2026-07-16
**Scope:** Core Application

## External APIs & Services
- **LLM Providers**: Google Gemini API (`google-genai`), OpenAI API (`openai`). Used for solving visual/multimodal challenges.
- **hCaptcha**: Target integration service (the application acts as a client interacting with hCaptcha widgets).
- **Roboflow**: Used for datasets and model versioning/hosting.

## Internal APIs / Webhooks
- Flask-based REST server available via `server` optional dependency (to provide captcha solving as a service locally).
