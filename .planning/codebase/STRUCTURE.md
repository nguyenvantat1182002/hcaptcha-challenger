# Codebase Structure

## Directory Layout
- **`src/hcaptcha_challenger/`**: The core package directory.
  - `agent/`: Contains the logic for the orchestrating agent that drives the captcha solving process.
  - `cli/`: Command-line interface definitions and entry points using `typer`.
  - `helper/`: Helper functions for image manipulation, video conversion, and grid generation.
  - `skills/`: Complex, reusable skills that the agent can utilize.
  - `tools/`: Specialized tools for specific challenge types (e.g., `challenge_classifier`, `image_classifier`, `spatial_bbox_reasoning`).
  - `models.py`: Data models and schemas using Pydantic.
  - `utils.py`: General utility functions used across the project.
- **`tests/`**: Contains the `pytest` test suite, organized by feature (tools, schemas, helpers).
- **`docs/`**: Project documentation in multiple languages.
- **`docker/`**: Contains Dockerfiles and `docker-compose.yaml` for containerized deployment.
- **`examples/`**: Demo scripts demonstrating various functionalities (e.g., `demo_captcha_agent.py`, `demo_camoufox.py`).

## Excluded Directories
- **`archive/`**: Legacy or deprecated code. This directory is explicitly ignored by the build system, linters, and this codebase map.

*(Note: The `archive` component has been explicitly excluded from this map.)*
