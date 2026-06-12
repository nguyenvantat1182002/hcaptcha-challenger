# Milestone 3: Agent Module Refactoring Requirements (Archived)

## 1. File Structure Extraction
- [x] Break down `c:\hcaptcha-challenger\src\hcaptcha_challenger\agent\challenger.py` into smaller files:
  - [x] `config.py`: Move `AgentConfig` class and related type definitions (`SINGLE_IGNORE_TYPE`, `IGNORE_REQUEST_TYPE_LIST`).
  - [x] `robotic_arm.py`: Move `RoboticArm` class and the bezier/delay helper functions (`_generate_bezier_trajectory`, `_generate_dynamic_delays`).
  - [x] `challenger.py` (Main): Retain `AgentV` (the core class handling network responses and solving flows) but update all imports to reference the newly extracted files.

## 2. Backward Compatibility
- [x] Ensure that the external API (how users import and use `AgentV` and `AgentConfig`) remains strictly unchanged.
- [x] Update `__init__.py` inside `src/hcaptcha_challenger/agent/` to properly expose `AgentConfig` and `AgentV` so that existing scripts continue to work seamlessly.

## 3. Verification
- [x] Verify that the refactored code passes `ruff` linter checks.
- [x] Verify that `pytest` (if available) passes or that the headless script from Milestone 2 can still be instantiated.

## Outcomes
- **Validated**: The refactoring was purely structural. The abstractions were successfully decoupled without impacting the dynamic OpenRouter inference layer introduced in v2.0.
