# Technology Stack
**Analysis Date:** 2026-05-01

## Languages
**Primary:**
- Python >= 3.10 - Used throughout the project for core logic, agents, and tools.

## Frameworks
**Core:**
- Pydantic & pydantic-settings - Used for data models (`src/hcaptcha_challenger/models.py`) and configuration (`src/hcaptcha_challenger/agent/config.py`).
- Typer - Powers the CLI interface (`src/hcaptcha_challenger/cli/main.py`).

**Automation:**
- DrissionPage - Used for browser control and interaction.
- Camoufox - Advanced browser fingerprinting and human-like interaction.

**Testing:**
- Pytest - Used for the test suite in `tests/`.

## Key Dependencies
- OpenCV (opencv-python) & Pillow - Core image processing libraries for CAPTCHA manipulation.
- Google GenAI (google-genai) - Official SDK for Gemini integration.
- OpenAI SDK - Used as a client for OpenRouter integration.
- Loguru - Structured logging.
- Tenacity - Retry logic for robust API interactions.
- Httpx - Async HTTP client.
