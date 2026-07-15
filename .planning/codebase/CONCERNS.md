# Concerns & Tech Debt

**Date:** 2026-07-16
**Scope:** Core Application

## Security & Fragility
- **Browser Automation Detection**: hCaptcha actively updates its bot detection. The library relies on tools like `camoufox` to stay undetected, which is an ongoing cat-and-mouse game.
- **Model Drift**: Local models (ResNet, YOLOv8) might need frequent retraining as hCaptcha introduces new types of image categories or UI variations.
- **LLM Rate Limits / Costs**: Dependence on OpenAI and Google Gemini APIs introduces potential cost and rate-limiting issues for heavy users.

## Maintenance
- Need to keep Playwright browser binaries updated.
- Some edge case challenges (`image_label_multiple_choice`) currently lack full support or rely on unstable workarounds.
