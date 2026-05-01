<!-- refreshed: 2025-04-18 -->
# Architecture

**Analysis Date:** 2025-04-18

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                            │
│           (Orchestration & Browser Control)                 │
│  `src/hcaptcha_challenger/agent/challenger.py`              │
└────────┬───────────────────┬───────────────────────┬────────┘
         │                   │                       │
         ▼                   ▼                       ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Skill Layer    │ │    Tool Layer    │ │   Helper Layer   │
│ (Prompt Mgmt)    │ │ (AI Reasoners)   │ │ (Visual Aids)    │
│ `skills/`        │ │ `tools/`         │ │ `helper/`        │
└────────┬─────────┘ └───────┬──────────┘ └──────────┬───────┘
         │                   │                       │
         └─────────┬─────────┴───────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│      (AI Providers, DrissionPage, Human Mouse)              │
│  `tools/internal/`, `agent/mouse.py`, `DrissionPage`        │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `AgentV` | High-level orchestrator; monitors network traffic, determines challenge state. | `src/hcaptcha_challenger/agent/challenger.py` |
| `RoboticArm` | Execution engine; captures screenshots, invokes tools, performs mouse actions. | `src/hcaptcha_challenger/agent/robotic.py` |
| `SkillManager` | Matches challenge questions to specialized prompt templates. | `src/hcaptcha_challenger/skills/manager.py` |
| `ImageClassifier` | Specialized reasoner for 3x3 binary classification challenges. | `src/hcaptcha_challenger/tools/image_classifier/` |
| `SpatialReasoner` | Base class for path/point reasoning using SCoT (Spatial Chain-of-Thought). | `src/hcaptcha_challenger/tools/spatial/base.py` |
| `ChallengeRouter` | Identifies challenge type and prompt from visual screenshot. | `src/hcaptcha_challenger/tools/challenge_router/` |
| `Human Mouse` | Algorithms for generating non-linear, human-like mouse trajectories. | `src/hcaptcha_challenger/agent/mouse.py` |

## Pattern Overview

**Overall:** Agentic Orchestration with Pluggable Intelligence.

**Key Characteristics:**
- **Intercept-First:** Uses network interception to get exact challenge payloads when possible, falling back to visual routing.
- **SCoT (Spatial Chain-of-Thought):** Employs visual aids (coordinate grids) overlaid on screenshots to help LLMs reason about spatial coordinates.
- **Layered Prompting:** High-level "skills" (prompts) are separated from the code logic, allowing for easy updates and specialization.

## Layers

**Agent Layer:**
- Purpose: Orchestrates the end-to-end solving process.
- Location: `src/hcaptcha_challenger/agent/`
- Contains: `AgentV` (lifecycle), `RoboticArm` (execution), `Mouse` (trajectories).
- Depends on: `skills/`, `tools/`, `helper/`, `models.py`.
- Used by: CLI and external library consumers.

**Tool Layer:**
- Purpose: Specialized AI logic for different challenge formats.
- Location: `src/hcaptcha_challenger/tools/`
- Contains: Image classifiers, spatial reasoners, and AI provider wrappers (Gemini, OpenRouter).
- Depends on: `models.py`, `tools/internal/`.

**Skill Layer:**
- Purpose: Management of prompt templates.
- Location: `src/hcaptcha_challenger/skills/`
- Contains: `SkillManager` and a library of markdown prompt templates.
- Depends on: `models.py`.

## Data Flow

### Primary Request Path

1. **Network Intercept:** `AgentV` detects `/getcaptcha` request via `page.listen`. (`agent/challenger.py:73`)
2. **Payload Parsing:** Intercepted body is unpacked via `msgpack` and validated into `CaptchaPayload`. (`agent/challenger.py:89`)
3. **Type Review:** `AgentV` determines the challenge type (e.g., `IMAGE_LABEL_BINARY`). (`agent/challenger.py:101`)
4. **Tool Invocation:** `RoboticArm` takes a screenshot and calls the corresponding tool (e.g., `ImageClassifier`). (`agent/robotic.py:326`)
5. **Prompting:** `SkillManager` provides the specific prompt for the tool based on the challenge question. (`agent/robotic.py:175`)
6. **Execution:** `RoboticArm` translates tool coordinates to pixel space and executes human-like clicks/drags. (`agent/robotic.py:348`)
7. **Verification:** `AgentV` waits for `/checkcaptcha` response to confirm success. (`agent/challenger.py:228`)

### Visual Fallback Path

1. **Detection Failure:** If network intercept fails, `RoboticArm` calls `check_challenge_type`. (`agent/robotic.py:228`)
2. **Visual Routing:** `ChallengeRouter` analyzes a screenshot of the `challenge-view` to identify the task. (`agent/robotic.py:246`)
3. **Proceed as Normal:** Once type is identified, it proceeds with Tool Invocation.

**State Management:**
- Stateless at the core; state is primarily managed within the `AgentV` instance during a single challenge lifecycle.
- Caching: Successful challenge responses and downloaded skills are cached to the filesystem.

## Key Abstractions

**`Reasoner`:**
- Purpose: Interface for AI-based decision making.
- Examples: `ImageClassifier`, `SpatialPathReasoner`.
- Pattern: Strategy Pattern for different challenge types.

**`DrissionPageMouse`:**
- Purpose: Adapter bridging human-like trajectory algorithms to browser-specific action APIs.
- Location: `src/hcaptcha_challenger/agent/robotic.py:53`.

## Entry Points

**CLI:**
- Location: `src/hcaptcha_challenger/cli/main.py`
- Triggers: User command line.
- Responsibilities: Configuration loading, environment setup, and launching the solver.

**Agent API:**
- Location: `src/hcaptcha_challenger/agent/challenger.py`
- Triggers: Instantiation by external scripts (e.g., `demo_normal_playwright.py`).
- Responsibilities: Monitoring browser frames and solving captchas.

## Architectural Constraints

- **Single-Threaded Loop:** Browser interaction and tool invocation are largely sequential within a single `AgentV` instance.
- **Iframe Isolation:** HCaptcha runs in multiple nested iframes (`frame=checkbox`, `frame=challenge`). The architecture uses `DrissionPage` to navigate these contexts.
- **Coordinate Normalization:** AI models operate on a `0-1000` normalized coordinate system to remain resolution-independent.

## Error Handling

**Strategy:** Fail-fast with retries for transient AI errors; fallback to visual detection for network interception gaps.

**Patterns:**
- `tenacity` retries for AI tool invocations.
- Custom exceptions like `HCaptchaBlockedError`.

---

*Architecture analysis: 2025-04-18*
