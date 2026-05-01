# External Integrations
**Analysis Date:** 2026-05-01

## APIs & External Services
**AI/LLM Providers:**
- Google Gemini API - Primary provider for challenge classification and spatial reasoning (`src/hcaptcha_challenger/tools/internal/providers/gemini.py`).
- OpenRouter - Used to access various LLMs via an OpenAI-compatible interface (`src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).

## Data Storage
**File Storage:**
- Local filesystem - The agent uses local directories for state and caching:
  - `tmp/.cache` - General cache.
  - `tmp/.challenge` - Storage for challenge-specific data.
  - `tmp/.captcha` - Storage for captcha responses.

## Authentication & Identity
**Auth Provider:**
- API Key based:
  - `GEMINI_API_KEY` - For Google Gemini services.
  - `OPENROUTER_API_KEY` - For OpenRouter services.

## CI/CD & Updates
- GitHub - The system supports auto-updating "skills" (rules) directly from the `QIN2DIM/hcaptcha-challenger` repository (`src/hcaptcha_challenger/agent/config.py`).
