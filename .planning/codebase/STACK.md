# Codebase Stack

## Languages
- Python >= 3.10

## Core Frameworks & Libraries
- **Browser Automation**: `playwright`, `camoufox`
- **Image Processing / Computer Vision**: `opencv-python` (>=4.11.0.88), `pillow` (>=11.1.0), `matplotlib` (>=3.10.8)
- **AI / LLM Integration**: `google-genai` (>=1.56.0)
- **CLI Framework**: `typer` (>=0.21.1)
- **Data Validation & Settings**: `pydantic-settings` (>=2.12.0)
- **HTTP Client**: `httpx[http2]` (>=0.28.1)
- **Serialization**: `msgpack` (>=1.1.1)
- **Logging**: `loguru` (>=0.7.3)

## Optional Dependencies
- **Server**: `fastapi[all]` (>=0.115.12)
- **Dataset Generation**: `typer`
- **Camoufox Enhancements**: `camoufox[geoip]` (>=0.4.11)

## Build System
- **Backend**: `hatchling`
- **Versioning**: `uv-dynamic-versioning`

*(Note: The `archive` component has been explicitly excluded from this map.)*
