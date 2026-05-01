# Requirements: HumanCursor Integration

## Functional Requirements
- **FR1: Trajectory Generation:** Use `humancursor` to generate all mouse trajectories for CAPTCHA interactions.
- **FR2: DrissionPage Integration:** Implement a `WebCursor` compatible adapter for DrissionPage `Actions` or directly use `humancursor`'s calculation logic with DrissionPage's low-level move commands.
- **FR3: Click Simulation:** Replace `human_click` with `humancursor`'s clicking logic.
- **FR4: Configuration Mapping:** Map `AgentConfig.MOUSE_SPEED` and other relevant settings to `humancursor` parameters.

## Non-Functional Requirements
- **NFR1: Realism:** Generated trajectories must pass basic "human-like" heuristic checks (non-linear, variable speed).
- **NFR2: Performance:** Trajectory generation must not introduce significant latency (<50ms per path).
- **NFR3: Maintainability:** Remove ~200 lines of custom trajectory code in favor of a library.

## Constraints
- Must work within the existing `DrissionPage` based `AgentV` orchestration.
- No new external system dependencies (beyond what `humancursor` requires).

## Success Criteria
- [ ] `src/hcaptcha_challenger/agent/mouse.py` logic is replaced with `humancursor` calls.
- [ ] `src/hcaptcha_challenger/agent/robotic.py` successfully uses the new movement engine.
- [ ] CAPTCHA solving flow completes successfully in a real browser environment.
- [ ] Existing tests (once updated) pass.
