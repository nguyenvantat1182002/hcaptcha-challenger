# Technology Stack

**Analysis Date:** 2026-04-30

## Languages

**Primary:**
- Python 3.10+ - core library and CLI in `src/hcaptcha_challenger/` (`pyproject.toml` `requires-python = ">=3.10"`).

**Secondary:**
- YAML - runtime and CI configuration in `docker/docker-compose.yaml`, `.github/workflows/*.yaml`, `src/hcaptcha_challenger/skills/rules.yaml`.
- Markdown - user and developer docs in `README.md`, `docs/README.md`, and `.cursor/skills/*/SKILL.md`.

## Runtime

**Environment:**
- CPython 3.10+ local runtime (`pyproject.toml`, `setup.py`).
- Container runtime supported via Docker Compose in `docker/docker-compose.yaml`.

**Package Manager:**
- `uv` (active workflow and lockfile): `uv.lock`, commands in `docs/README.md`.
- `pip` compatible packaging: `pyproject.toml` and `setup.py`.
- Lockfile: present (`uv.lock`).

## Frameworks

**Core:**
- Pydantic v2 + pydantic-settings - typed models and env-backed config in `src/hcaptcha_challenger/models.py`, `src/hcaptcha_challenger/agent/config.py`.
- Typer - CLI framework in `src/hcaptcha_challenger/cli/main.py`, `src/hcaptcha_challenger/cli/solver.py`, `src/hcaptcha_challenger/cli/dataset.py`.
- DrissionPage + Playwright - browser automation used by the agent in `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/cli/dataset.py`.

**Testing:**
- Pytest + pytest-asyncio - test runner and async test support configured in `pyproject.toml` and used in `tests/`.

**Build/Dev:**
- Hatchling + uv-dynamic-versioning - package build/versioning in `pyproject.toml` (`[build-system]`, `[tool.hatch.version]`).
- Ruff - linting in `pyproject.toml` (`[tool.ruff]`).
- Black - formatting in `pyproject.toml` (`[tool.black]`).
- Ty (`ty.toml`) - static type checking configuration.

## Key Dependencies

**Critical:**
- `google-genai` - Gemini multimodal client in `src/hcaptcha_challenger/tools/internal/providers/gemini.py`.
- `openai` - OpenRouter transport client in `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`.
- `opencv-python` / `pillow` / `matplotlib` - image processing/visualization in `src/hcaptcha_challenger/helper/*.py`.
- `drissionpage` + `playwright` - browser control and data collection in `src/hcaptcha_challenger/agent/robotic.py`, `src/hcaptcha_challenger/cli/dataset.py`.

**Infrastructure:**
- `httpx` - HTTP client for remote skill updates in `src/hcaptcha_challenger/skills/manager.py`.
- `loguru` - structured logging across runtime modules (for example `src/hcaptcha_challenger/agent/challenger.py`).
- `msgpack` - challenge payload serialization in `src/hcaptcha_challenger/agent/challenger.py`.
- `pyyaml` - skill rule manifest parsing in `src/hcaptcha_challenger/skills/manager.py`.
- `tenacity` - retry strategy in AI providers (`src/hcaptcha_challenger/tools/internal/providers/gemini.py`, `src/hcaptcha_challenger/tools/internal/providers/openrouter.py`).

## Configuration

**Environment:**
- Runtime settings are loaded through `AgentConfig` (`src/hcaptcha_challenger/agent/config.py`) with `env_file=".env"`.
- Example env templates are provided at `examples/.env.example` and `docker/.env.example`.
- Key runtime config includes model selection, timeout controls, and cache/challenge directories in `src/hcaptcha_challenger/agent/config.py`.

**Build:**
- Packaging/build config: `pyproject.toml`, `setup.py`.
- Container config: `docker/Dockerfile`, `docker/docker-compose.yaml`.
- CI config: `.github/workflows/python-pytest.yaml`, `.github/workflows/publish.yaml`, `.github/workflows/sentinel.yaml`, `.github/workflows/collector.yaml`.

## Platform Requirements

**Development:**
- Python >=3.10 and `uv` toolchain expected by docs (`docs/README.md`).
- Browser automation dependencies required for dataset collection/tests (`playwright` and Chromium install in `.github/workflows/*.yaml`).

**Production:**
- Python package distribution via PyPI metadata in `pyproject.toml`.
- Optional container deployment to GHCR/Docker environments (`.github/workflows/publish.yaml`, `docker/docker-compose.yaml`).

---

*Stack analysis: 2026-04-30*
