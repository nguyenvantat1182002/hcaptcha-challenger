# Phase 7: Code Extraction (Agent Module Refactoring)

## Objective
Dismantle the monolithic `challenger.py` file (>1000 lines) within `src/hcaptcha_challenger/agent/` by extracting `AgentConfig`, type aliases, and the `RoboticArm` class into dedicated standalone files (`config.py` and `robotic_arm.py`), leaving only the core `AgentV` loop in `challenger.py`.

## Context
See `.planning/implementation_plan.md` for technical design. The refactoring will maintain strict backward compatibility by exposing `AgentConfig` and `AgentV` through `src/hcaptcha_challenger/agent/__init__.py`.

## Steps

### Step 1: Extract `config.py`
- Create `src/hcaptcha_challenger/agent/config.py`.
- Move the following elements from `challenger.py`:
  - `SINGLE_IGNORE_TYPE`
  - `IGNORE_REQUEST_TYPE_LIST`
  - `AgentConfig`
- Ensure all necessary imports (`pydantic`, `Path`, `ChallengeTypeEnum`, `FastShotModelType`, etc.) are included in `config.py`.

### Step 2: Extract `robotic_arm.py`
- Create `src/hcaptcha_challenger/agent/robotic_arm.py`.
- Move the following elements from `challenger.py`:
  - `_generate_bezier_trajectory`
  - `_generate_dynamic_delays`
  - `RoboticArm`
- Ensure all necessary imports (`AgentConfig`, `ChallengeRouter`, `ImageClassifier`, `asyncio`, `playwright`, etc.) are included.
- Import `AgentConfig` from `.config`.

### Step 3: Refactor `challenger.py` and `__init__.py`
- Remove the extracted code from `challenger.py`.
- In `challenger.py`, import `AgentConfig` from `.config` and `RoboticArm` from `.robotic_arm`.
- In `src/hcaptcha_challenger/agent/__init__.py`, update the imports to fetch `AgentConfig` from `.config` and `AgentV` from `.challenger`.

### Step 4: Verification
- Run `uv run ruff check src/hcaptcha_challenger/agent/` to assert no import errors or undefined variables.
- Run `uv run pytest tests/test_openrouter_e2e.py` to ensure runtime initialization of `AgentConfig` and the system continues to work correctly.
