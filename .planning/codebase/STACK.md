# Technology Stack

**Analysis Date:** 2026-05-01

## Languages

**Primary:**
- Python 3.10+ - Core logic, CLI, and agent implementation.

**Secondary:**
- JavaScript - Used for in-browser scripts like `src/hcaptcha_challenger/helper/assets/scripts/mouse_visualizer.js`.
- Shell/PowerShell - Deployment scripts and utility commands.

## Runtime

**Environment:**
- Python 3.10 to 3.13 (as per `pyproject.toml`).

**Package Manager:**
- `uv` (recommended, `uv.lock` present)
- `pip` / `setuptools` (`setup.py` present)
- `hatch` (build backend)

## Frameworks

**Core:**
- `DrissionPage` 4.1.1+ - High-performance browser automation for interacting with hCaptcha.
- `Pydantic` & `pydantic-settings` 2.12+ - Data validation and configuration management.
- `FastAPI` (optional) - API server for remote solver invocation.
- `Typer` - CLI framework for the `hc` command.

**Testing:**
- `pytest` - Primary test runner.
- `pytest-asyncio` - Async test support.

**Build/Dev:**
- `hatchling` - Build system.
- `ruff` - Linting and formatting.
- `black` - Code formatting.

## Key Dependencies

**Critical:**
- `google-genai` >= 1.56.0 - Direct integration with Google Gemini models.
- `openai` >= 2.32.0 - Used as a client for OpenRouter and OpenAI-compatible APIs.
- `humancursor` >= 1.1.5 - Human-like mouse movement simulation.
- `tenacity` - Retry logic for API calls and browser operations.
- `loguru` - Structured logging.

**Infrastructure:**
- `opencv-python` & `pillow` - Image processing and manipulation.
- `matplotlib` - Visualization and coordinate grid generation.
- `msgpack` - Binary serialization for hCaptcha payload decoding.
- `httpx` - Modern HTTP client with HTTP/2 support.

## Configuration

**Environment:**
- Configured via `.env` file and environment variables using `pydantic-settings`.
- Key configs: `OPENROUTER_API_KEY`.

**Build:**
- `pyproject.toml` - Main project configuration.
- `ty.toml` - Likely tool-specific configuration.

## Platform Requirements

**Development:**
- Python 3.10+
- Browser environment (Chromium-based) for automation.

**Production:**
- Docker support (`Dockerfile` present in `docker/`).
- Support for various hCaptcha challenge types (binary label, area select, drag-drop).

---

*Stack analysis: 2026-05-01*
