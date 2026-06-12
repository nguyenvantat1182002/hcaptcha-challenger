# Phase 3: Tools & Integration Context

## Decisions

1. **Tooling Strategy**: Instead of a generic dummy tool (like `get_weather`), we will implement a realistic, domain-specific tool for `hcaptcha-challenger` using Pydantic. Specifically, a tool named `click_coordinates` that simulates selecting coordinates on a captcha image based on reasoning.
2. **Headless Testing (`headless.py`)**: The test script will be fully automated rather than an interactive REPL. It will instantiate the agent, attach the `click_coordinates` tool, register `stream:delta` and `tool:call` event listeners, and fire a predefined hardcoded prompt (e.g., asking the agent to click specific coordinates based on a mock task).

## Next Steps
This context finalizes the requirements for Phase 3. Downstream planners will use this to generate `3-PLAN.md`.
