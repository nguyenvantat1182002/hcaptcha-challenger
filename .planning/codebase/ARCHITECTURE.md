<!-- refreshed: 2025-05-15 -->
# Architecture

**Analysis Date:** 2025-05-15

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                            │
│           `src/hcaptcha_challenger/agent`                    │
├──────────────────┬──────────────────┬───────────────────────┤
│    AgentV        │    RoboticArm    │     AgentConfig       │
│  `challenger.py` │   `robotic.py`   │     `config.py`       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reasoning Layer                           │
│           `src/hcaptcha_challenger/tools`                   │
│  `ImageClassifier` `SpatialPathReasoner` `ChallengeRouter`   │
└─────────────────────────────────────────────────────────────┘
         │                  │
         ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill Layer (Prompts)     │  Provider Layer (LLM/Vision)   │
│ `skills/manager.py`        │ `tools/internal/providers`     │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| AgentV | Orchestrates the captcha solving workflow, intercepts network traffic, and manages task queues. | `src/hcaptcha_challenger/agent/challenger.py` |
| RoboticArm | Translates high-level solving decisions into browser actions (clicks, drags) with human-like mouse movements. | `src/hcaptcha_challenger/agent/robotic.py` |
| Reasoner (Base) | Abstract base class for all reasoning tools, managing prompt loading and provider interaction. | `src/hcaptcha_challenger/tools/internal/base.py` |
| SkillManager | Manages prompt templates (skills) with layered priority (User > Cache > Built-in) and remote update support. | `src/hcaptcha_challenger/skills/manager.py` |
| DrissionPageMouse | Adapter bridging high-level mouse trajectories to low-level browser CDP commands. | `src/hcaptcha_challenger/agent/robotic.py` |
| Models | Centralized data structures and Pydantic schemas for captcha payloads and responses. | `src/hcaptcha_challenger/models.py` |

## Pattern Overview

**Overall:** Agentic Multimodal Reasoning

**Key Characteristics:**
- **Asynchronous Interception:** Uses `DrissionPage` to listen for `/getcaptcha` (payload) and `/checkcaptcha` (verification) requests in the background.
- **Human-like Interaction:** Employs Bezier curve trajectories for mouse movements and randomized delays to bypass anti-bot detections.
- **Normalized Coordinate Mapping:** Vision models operate on a 0-1000 normalized grid, which is mapped to real viewport coordinates by the `RoboticArm`.
- **Decoupled Reasoning:** Solvers (Tools) are independent of the browser agent, allowing them to be tested or used in isolation.

## Layers

**Agent Layer:**
- Purpose: Orchestration and browser state management.
- Location: `src/hcaptcha_challenger/agent`
- Contains: `AgentV`, `RoboticArm`, `AgentConfig`.
- Depends on: `Reasoning Layer`, `DrissionPage`.
- Used by: CLI, external implementations.

**Reasoning Layer:**
- Purpose: Decision making using Multimodal Large Language Models (MLLMs).
- Location: `src/hcaptcha_challenger/tools`
- Contains: `ImageClassifier`, `SpatialPathReasoner`, `SpatialPointReasoner`, `ChallengeRouter`.
- Depends on: `Provider Layer`, `Skill Layer`.
- Used by: `Agent Layer`.

**Skill Layer:**
- Purpose: Domain-specific knowledge and prompt engineering.
- Location: `src/hcaptcha_challenger/skills`
- Contains: `SkillManager`, YAML rules, and Markdown templates.
- Depends on: `models.py`.
- Used by: `Reasoning Layer`.

**Provider Layer:**
- Purpose: Interface with LLM APIs (OpenRouter, Gemini, etc.).
- Location: `src/hcaptcha_challenger/tools/internal/providers`
- Contains: `OpenRouterProvider`, `GeminiProvider`.
- Depends on: `httpx`, `openai`, `google-genai`.
- Used by: `Reasoning Layer`.

## Data Flow

### Primary Request Path (Solving a Challenge)

1. **Interception:** `AgentV` detects `/getcaptcha` request and extracts the `msgpack` payload (`src/hcaptcha_challenger/agent/challenger.py:_task_handler`).
2. **Identification:** `RoboticArm` identifies the challenge type (Binary, Select, Drag-Drop) from the payload or via visual routing if payload is missing (`src/hcaptcha_challenger/agent/robotic.py:check_challenge_type`).
3. **Capture:** `RoboticArm` takes a screenshot of the `challenge-view` element and generates a coordinate grid overlay if needed (`src/hcaptcha_challenger/agent/robotic.py:_capture_spatial_mapping`).
4. **Prompting:** `SkillManager` retrieves the appropriate prompt template based on the challenge text (`src/hcaptcha_challenger/skills/manager.py:get_skill`).
5. **Reasoning:** The specific `Reasoner` (Tool) sends the image and prompt to the MLLM provider and receives structured results (`src/hcaptcha_challenger/tools/internal/base.py:__call__`).
6. **Execution:** `RoboticArm` scales the normalized coordinates to pixel coordinates and executes human-like clicks or drags (`src/hcaptcha_challenger/agent/robotic.py:challenge_image_*`).
7. **Verification:** `AgentV` waits for the `/checkcaptcha` response to confirm success or failure (`src/hcaptcha_challenger/agent/challenger.py:wait_for_challenge`).

## Key Abstractions

**Reasoner:**
- Purpose: Encapsulates the logic for a specific type of visual reasoning task.
- Examples: `src/hcaptcha_challenger/tools/image_classifier/__init__.py`, `src/hcaptcha_challenger/tools/spatial/path.py`.
- Pattern: Strategy Pattern / Command Pattern.

**SkillRule:**
- Purpose: Defines when a specific prompt template should be used based on regex matching of the challenge question.
- Examples: Defined in `src/hcaptcha_challenger/skills/rules.yaml`.

## Entry Points

**CLI (hc):**
- Location: `src/hcaptcha_challenger/cli/main.py`
- Triggers: User command line input.
- Responsibilities: Routing to `solver` or `dataset` modules.

**AgentV.wait_for_challenge():**
- Location: `src/hcaptcha_challenger/agent/challenger.py`
- Triggers: Called by automation scripts after triggering a captcha.
- Responsibilities: Main loop for solving the currently active challenge.

## Architectural Constraints

- **Threading:** `AgentV` runs a background thread for network interception (`_task_handler`), while the main thread handles browser interaction.
- **Global state:** Configuration is managed via a singleton-like `AgentConfig` instance passed throughout the system.
- **Coordinate System:** Strict adherence to the 0-1000 normalized coordinate system for all spatial reasoning tools.

## Anti-Patterns

### Direct Browser Manipulation
**What happens:** Using `element.click()` or `page.click()` directly.
**Why it's wrong:** Detected easily by anti-bot systems as non-human.
**Do this instead:** Use `RoboticArm.click_element()` or `RoboticArm.click_at()` which use `human_move` and `human_click`.

### Hardcoded Prompts
**What happens:** Defining LLM prompts directly in Python strings.
**Why it's wrong:** Makes it difficult to update or localize prompts without changing code.
**Do this instead:** Define templates in `src/hcaptcha_challenger/skills/library/` and manage them via `SkillManager`.

## Error Handling

**Strategy:** Fail fast on configuration/network issues; Retry on intermittent reasoning failures.

**Patterns:**
- **Tenacity Retries:** Used in `RoboticArm` for capturing spatial mapping to handle rendering delays.
- **Fallback Type Detection:** If payload parsing fails, the system falls back to visual classification via `ChallengeRouter`.

## Cross-Cutting Concerns

**Logging:** Uses `loguru` for structured logging across all layers. Logs are stored by date in `src/hcaptcha_challenger/logs/`.
**Validation:** `pydantic` is used for all data models and configuration settings.

---

*Architecture analysis: 2025-05-15*
