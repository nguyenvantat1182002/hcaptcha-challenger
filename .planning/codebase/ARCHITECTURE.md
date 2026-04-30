<!-- refreshed: 2026-04-30 -->
# Architecture

**Analysis Date:** 2026-04-30

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                   CLI / Consumer Surface                    │
├──────────────────┬──────────────────┬───────────────────────┤
│   Public API     │   Typer CLI      │   Test Harness        │
│`src/hcaptcha_... │`src/hcaptcha_... │`tests/`               │
│ __init__.py`     │ cli/main.py`     │                       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agent Orchestration Layer                  │
│  `src/hcaptcha_challenger/agent/challenger.py`              │
│  `src/hcaptcha_challenger/agent/robotic.py`                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│          Tooling + Provider + External Browser/LLM          │
│ `src/hcaptcha_challenger/tools/` + OpenRouter + DrissionPage│
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI command router | Entrypoint that mounts `dataset` and `solver` subcommands | `src/hcaptcha_challenger/cli/main.py` |
| Challenge lifecycle controller | Listens for captcha packets, selects solving strategy, waits for verdict | `src/hcaptcha_challenger/agent/challenger.py` |
| Browser action executor | Captures challenge screenshots, invokes reasoning tools, performs click/drag actions | `src/hcaptcha_challenger/agent/robotic.py` |
| Tool facade package | Exposes challenge router, classifier, and spatial reasoners as stable imports | `src/hcaptcha_challenger/tools/__init__.py` |
| LLM provider adapter | Converts image inputs + schema into OpenRouter API calls and parses typed output | `src/hcaptcha_challenger/tools/internal/providers/openrouter.py` |
| Domain schema layer | Defines challenge enums, payload/response models, and structured output contracts | `src/hcaptcha_challenger/models.py` |

## Pattern Overview

**Overall:** Layered orchestration with typed tool adapters.

**Key Characteristics:**
- Entry surfaces are thin (`cli`, package exports), with operational logic concentrated in `agent` and `tools`.
- LLM integrations are wrapped behind typed reasoners (`Reasoner`, `SpatialReasoner`) rather than called directly.
- Captcha state is treated as typed contracts (`CaptchaPayload`, `CaptchaResponse`, challenge result models).

## Layers

**Interface Layer:**
- Purpose: Accept user/system triggers.
- Location: `src/hcaptcha_challenger/cli/` and `src/hcaptcha_challenger/__init__.py`
- Contains: Typer apps, command handlers, public exports.
- Depends on: `agent`, `tools`, `helper`, `models`.
- Used by: End users (`hc ...`) and library consumers (`import hcaptcha_challenger`).

**Orchestration Layer:**
- Purpose: Coordinate browser events, challenge classification, and action execution.
- Location: `src/hcaptcha_challenger/agent/`
- Contains: `AgentV`, `RoboticArm`, config, mouse movement logic.
- Depends on: `models`, `tools`, `skills`, DrissionPage.
- Used by: CLI and external code that constructs `AgentV`.

**Reasoning Tool Layer:**
- Purpose: Encapsulate challenge-specific AI reasoning operations.
- Location: `src/hcaptcha_challenger/tools/`
- Contains: `ChallengeRouter`, `ImageClassifier`, spatial reasoners.
- Depends on: `tools/internal`, `models`, markdown prompt files.
- Used by: `RoboticArm` in `src/hcaptcha_challenger/agent/robotic.py`.

**Provider Layer:**
- Purpose: Implement provider protocol and network I/O to model backends.
- Location: `src/hcaptcha_challenger/tools/internal/providers/`
- Contains: `ChatProvider` protocol and `OpenRouterProvider`.
- Depends on: `openai` SDK, `pydantic`.
- Used by: `Reasoner` base class in `src/hcaptcha_challenger/tools/internal/base.py`.

**Support Layer:**
- Purpose: Shared utility and helper modules for grid generation, prompts, logging, and skill matching.
- Location: `src/hcaptcha_challenger/helper/`, `src/hcaptcha_challenger/skills/`, `src/hcaptcha_challenger/utils.py`
- Contains: image/grid helpers, rules loading, logging bootstrap.
- Depends on: matplotlib, yaml/httpx, loguru.
- Used by: CLI and agent orchestration.

## Data Flow

### Primary Request Path

1. CLI entrypoint dispatches command tree (`src/hcaptcha_challenger/cli/main.py:82`).
2. Solver/agent setup builds config + browser frame and creates `AgentV` (`src/hcaptcha_challenger/agent/challenger.py:34`).
3. Packet listener captures `/getcaptcha` + `/checkcaptcha`, parses to typed models (`src/hcaptcha_challenger/agent/challenger.py:65`).
4. `AgentV` resolves challenge type and delegates to `RoboticArm` strategy (`src/hcaptcha_challenger/agent/challenger.py:140`).
5. `RoboticArm` captures screenshot, invokes tool reasoner, then performs click/drag actions (`src/hcaptcha_challenger/agent/robotic.py:362`).
6. Tool call reaches provider `generate_with_images` and returns typed result (`src/hcaptcha_challenger/tools/internal/providers/openrouter.py:62`).
7. Agent waits for check response queue and returns `ChallengeSignal` (`src/hcaptcha_challenger/agent/challenger.py:193`).

### Dataset Analysis Flow

1. Dataset command receives `dataset cost` or `dataset check` (`src/hcaptcha_challenger/cli/dataset.py:27`).
2. Command scans challenge artifacts in `tmp`/custom path (`src/hcaptcha_challenger/cli/dataset.py:69`).
3. Helper functions aggregate stats and report with rich tables (`src/hcaptcha_challenger/cli/dataset.py:83`).

**State Management:**
- Runtime state is mostly in-memory queues and object fields on `AgentV` (`_captcha_payload_queue`, `_captcha_response_queue`).
- Persistent operational artifacts are file-based caches under `tmp/.cache`, `tmp/.challenge`, and `tmp/.captcha` from `AgentConfig`.

## Key Abstractions

**Typed Challenge Contracts:**
- Purpose: Keep all challenge I/O strongly structured.
- Examples: `src/hcaptcha_challenger/models.py`
- Pattern: Pydantic models + enums at module boundary.

**Reasoner Base Class:**
- Purpose: Standardize provider invocation and response caching.
- Examples: `src/hcaptcha_challenger/tools/internal/base.py`, `src/hcaptcha_challenger/tools/spatial/base.py`
- Pattern: Generic abstract base class with provider composition.

**Skill Routing:**
- Purpose: Map challenge text + job type to reusable prompt templates.
- Examples: `src/hcaptcha_challenger/skills/manager.py`, `src/hcaptcha_challenger/skills/schema.py`
- Pattern: Rules manifest + layered source priority (user > cache > built-in).

## Entry Points

**Package script (`hc`):**
- Location: `pyproject.toml`
- Triggers: Shell command `hc`
- Responsibilities: Invoke `hcaptcha_challenger.cli.main:main`.

**CLI root app:**
- Location: `src/hcaptcha_challenger/cli/main.py`
- Triggers: `hc` execution
- Responsibilities: Attach subcommands and route to dataset/solver flows.

**Library import surface:**
- Location: `src/hcaptcha_challenger/__init__.py`
- Triggers: Python import usage
- Responsibilities: Expose `AgentV`, `AgentConfig`, and tool classes for embedding.

## Architectural Constraints

- **Threading:** Mixed model: background thread for network packet listener in `AgentV` plus synchronous wait loops.
- **Global state:** Logger is globally initialized in `src/hcaptcha_challenger/__init__.py`; environment-backed settings are loaded in `AgentConfig`.
- **Circular imports:** Not detected in scanned core modules.
- **Provider contract:** Tool implementations assume `ChatProvider.generate_with_images` behavior; new providers must match protocol in `src/hcaptcha_challenger/tools/internal/providers/protocol.py`.

## Anti-Patterns

### Duplicate Cost Command Implementation

**What happens:** `src/hcaptcha_challenger/cli/solver.py` and `src/hcaptcha_challenger/cli/dataset.py` both implement the same `cost` command body.
**Why it's wrong:** Logic divergence risk and duplicated maintenance effort.
**Do this instead:** Keep `cost` command in one module and delegate from the other via shared function in `src/hcaptcha_challenger/helper/cost_calculator.py`.

### Async Contract Drift Between Tests and Tool APIs

**What happens:** Core tools are synchronous callables, while several tests still use `await` patterns.
**Why it's wrong:** Test expectations can drift from production behavior and mask integration issues.
**Do this instead:** Align tests in `tests/` with current synchronous call signatures used by `RoboticArm` in `src/hcaptcha_challenger/agent/robotic.py`.

## Error Handling

**Strategy:** Guarded operation with fallback and soft-fail logging.

**Patterns:**
- Use retries for network/provider boundaries (`tenacity` in `openrouter.py` and `robotic.py`).
- Use fallback branch to visual challenge routing when payload parse fails (`AgentV._review_challenge_type`).
- Catch-and-log file write/cache failures instead of terminating challenge loop.

## Cross-Cutting Concerns

**Logging:** Centralized with Loguru initialization in `src/hcaptcha_challenger/utils.py` and startup in `src/hcaptcha_challenger/__init__.py`.
**Validation:** Pydantic schemas in `src/hcaptcha_challenger/models.py` and settings validation in `src/hcaptcha_challenger/agent/config.py`.
**Authentication:** API key read from environment/config (`OPENROUTER_API_KEY`) and passed into tool providers by `RoboticArm`.

---

*Architecture analysis: 2026-04-30*
