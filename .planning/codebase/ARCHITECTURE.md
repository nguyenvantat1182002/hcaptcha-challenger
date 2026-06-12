# Architecture

## High-Level Design
`hcaptcha-challenger` is designed as an agentic workflow system that uses multimodal large language models to interact with and solve hCaptcha challenges. It acts as a bridge between browser automation and AI reasoning.

## Core Components
- **Agent Layer**: Orchestrates the challenge-solving process. It observes the captcha state, decides on the required action, and executes it.
- **Tools / Skills Layer**: Specialized modules designed to handle specific types of tasks, such as bounding box reasoning, point reasoning, image classification, and challenge type identification.
- **Helper / Utilities Layer**: Functions for image processing (e.g., creating comparison images, drawing coordinate grids), visual attention point visualization, and environment generation.
- **CLI Interface**: A `typer`-based command-line interface allowing users to run the agent, start a server, or trigger specific workflows.
- **Data Models**: Pydantic models (in `models.py`) used for structured data validation and communication between different components.

## Data Flow
1. **Observation**: Playwright/Camoufox extracts the captcha challenge from the webpage (images, instructions).
2. **Analysis**: The challenge is classified, and the appropriate tool (e.g., spatial reasoning, image classification) is selected.
3. **Reasoning**: The data is sent to a multimodal LLM (via Google GenAI) to determine the solution (e.g., which images to click, where to draw bounding boxes).
4. **Execution**: The browser automation framework performs the clicks or drag-and-drops based on the LLM's response.

*(Note: The `archive` component has been explicitly excluded from this map.)*
