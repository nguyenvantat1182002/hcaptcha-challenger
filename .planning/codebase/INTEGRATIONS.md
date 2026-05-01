# External Integrations

**Analysis Date:** 2026-05-01

## APIs & External Services

**Large Language Model (LLM) Gateways:**
- **OpenRouter** - Primary gateway for accessing multiple LLM models (Gemini, GPT, etc.) used for challenge reasoning.
  - SDK/Client: `openai` (configured with OpenRouter base URL)
  - Auth: `OPENROUTER_API_KEY` (env var)
  - Implementation: `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`

**Native LLM Providers:**
- **Google Gemini** - Direct integration with Google's Gemini models for vision and reasoning tasks.
  - SDK/Client: `google-genai`
  - Auth: API Key passed via configuration.
  - Implementation: `src/hcaptcha_challenger/tools/internal/providers/gemini.py`

**hCaptcha Services:**
- **hCaptcha API** - The target service being solved. The agent interacts with `getcaptcha` and `checkcaptcha` endpoints.
  - Integration: intercepted via browser automation and `msgpack` decoding.
  - Implementation: `src/hcaptcha_challenger/agent/challenger.py`

## Data Storage

**Databases:**
- **Not applicable** (No persistent database detected).

**File Storage:**
- **Local filesystem** - Used for caching, logging, and storing artifacts.
  - Cache: `tmp/.cache/`
  - Challenges: `tmp/.challenge/`
  - Logs: `src/hcaptcha_challenger/logs/`
  - Captcha responses: `tmp/.captcha/`

**Caching:**
- **Local filesystem** - Reasoning results and spatial grids are cached locally.

## Authentication & Identity

**Auth Provider:**
- **Not applicable** - The project focuses on solving hCaptcha challenges, not internal user authentication.

## Monitoring & Observability

**Error Tracking:**
- **Loguru** - Local structured logging for error and runtime tracking.

**Logs:**
- **File-based logging** - Separate logs for `runtime`, `error`, and `serialize` data.
- Implementation: `src/hcaptcha_challenger/utils.py` (`init_log` function).

## CI/CD & Deployment

**Hosting:**
- **Docker** - Containerized deployment supported via `Dockerfile`.

**CI Pipeline:**
- **GitHub Actions** - Workflows for publishing and testing (`.github/workflows/`).

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` - Critical for LLM-based reasoning.
- `LOG_LEVEL` - Controls logging verbosity.

**Secrets location:**
- `.env` file (loaded via `pydantic-settings`).

## Webhooks & Callbacks

**Incoming:**
- **hCaptcha traffic** - Intercepted via `DrissionPage` listeners in `src/hcaptcha_challenger/agent/challenger.py`.

**Outgoing:**
- **LLM Requests** - Outgoing calls to OpenRouter or Google Gemini APIs.

---

*Integration audit: 2026-05-01*
