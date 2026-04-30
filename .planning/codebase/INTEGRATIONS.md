# External Integrations

**Analysis Date:** 2026-04-30

## APIs & External Services

**LLM Providers:**
- OpenRouter API - multimodal reasoning backend for core `Reasoner` classes.
  - SDK/Client: `openai` client configured with `base_url="https://openrouter.ai/api/v1"` in `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`.
  - Auth: `OPENROUTER_API_KEY` via `src/hcaptcha_challenger/agent/config.py`.
- Google Gemini API - direct provider for image + structured response generation.
  - SDK/Client: `google-genai` in `src/hcaptcha_challenger/tools/internal/providers/gemini.py`.
  - Auth: API key passed at runtime (examples/tests use `GEMINI_API_KEY` in `tests/test_tools_common.py`, `docker/.env.example`).

**Browser/Challenge Endpoints:**
- hCaptcha demo/challenge domains - browser agent targets and iframe selectors.
  - SDK/Client: browser control via `drissionpage` and `playwright` in `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/cli/dataset.py`.
  - Auth: Not applicable (site interaction, no direct API token in code).

**Remote Skill Distribution:**
- GitHub Raw content - fetches skill rules/templates dynamically.
  - SDK/Client: `httpx` in `src/hcaptcha_challenger/skills/manager.py`; URL generation in `src/hcaptcha_challenger/skills/schema.py`.
  - Auth: No auth required for public raw endpoints.

## Data Storage

**Databases:**
- Not detected in active `src/hcaptcha_challenger/` code (no SQL/NoSQL client usage in runtime path).
  - Connection: Not applicable.
  - Client: Not applicable.

**File Storage:**
- Local filesystem only.
  - Runtime cache/challenge output directories in `src/hcaptcha_challenger/agent/config.py` (`tmp/.cache`, `tmp/.challenge`, `tmp/.captcha`).
  - Optional response cache writes in `src/hcaptcha_challenger/tools/internal/providers/gemini.py` and `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`.

**Caching:**
- Local disk cache (skills/templates and model responses), no external cache service detected.

## Authentication & Identity

**Auth Provider:**
- Custom API key configuration through environment variables (no OAuth/OIDC provider integration in runtime code).
  - Implementation: `pydantic-settings` `BaseSettings` in `src/hcaptcha_challenger/agent/config.py` with `SecretStr` handling for `OPENROUTER_API_KEY`.

## Monitoring & Observability

**Error Tracking:**
- No external error tracker detected (for example Sentry/Datadog not used in active source).

**Logs:**
- Application logging through `loguru` across agent/tools modules (for example `src/hcaptcha_challenger/agent/challenger.py`, `src/hcaptcha_challenger/tools/internal/providers/*.py`).

## CI/CD & Deployment

**Hosting:**
- Python package distribution (PyPI package metadata in `pyproject.toml`).
- Container image publishing to GitHub Container Registry (`ghcr.io`) in `.github/workflows/publish.yaml`.

**CI Pipeline:**
- GitHub Actions:
  - Test workflow: `.github/workflows/python-pytest.yaml`.
  - Collector/sentinel automation: `.github/workflows/collector.yaml`, `.github/workflows/sentinel.yaml`.
  - Publish workflow: `.github/workflows/publish.yaml`.

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` (`src/hcaptcha_challenger/agent/config.py`).
- `GEMINI_API_KEY` (example/test usage in `docker/.env.example`, `tests/test_tools_common.py`).
- Operational/CI vars used by automation workflows and scripts:
  - `GITHUB_TOKEN` (`archive/automation/*.py`, `.github/workflows/*.yaml`).
  - `SITEKEY_*`, `COLLECTOR_PER_TIMES`, `SENTINEL_PER_TIMES` (`.github/workflows/sentinel.yaml`, `.github/workflows/collector.yaml`).
  - `LOG_LEVEL` (`src/hcaptcha_challenger/utils.py`).

**Secrets location:**
- Local env files for user runtime (for example `.env` expected by `AgentConfig`; templates in `docker/.env.example`, `examples/.env.example`).
- GitHub Actions secrets for CI (for example `secrets.SENTINEL_ACCESS_TOKEN` in workflows).

## Webhooks & Callbacks

**Incoming:**
- None detected in active runtime package (`src/hcaptcha_challenger/`).

**Outgoing:**
- No webhook push integration detected in active runtime package.
- Outgoing HTTP requests are API calls to LLM providers and GitHub raw content (`src/hcaptcha_challenger/tools/internal/providers/*.py`, `src/hcaptcha_challenger/skills/manager.py`).

---

*Integration audit: 2026-04-30*
