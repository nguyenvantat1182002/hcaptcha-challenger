# Architecture

The application is structured as an AI agent designed to interact with and solve hCaptcha challenges.

## Core Components
1. **Agent Orchestrator**: Manages the end-to-end lifecycle of the challenge, using browser automation (Playwright/Camoufox) to navigate, trigger, and intercept hCaptcha elements.
2. **Vision / Reasoning Models**: Uses external Multimodal LLMs (Google GenAI, OpenAI) to analyze the hCaptcha images (prompts, targets, grids).
3. **Computer Vision Helpers**: Uses OpenCV and Pillow to slice, grid, and analyze challenge images before sending them to the LLM, reducing hallucination and improving coordinate accuracy.
4. **Tools / Skills**: Specific modules mapping to different types of challenges (e.g., bounding box reasoning, path reasoning, point reasoning).
5. **CLI Interface**: A Typer-based command-line tool (`hc`) for triggering the agent, testing, and dataset management.
