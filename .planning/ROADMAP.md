# Roadmap: HumanCursor Integration

## Phase 1: Foundation & Research
- [x] Analyze current `mouse.py` and `robotic.py` logic.
- [x] Research `humancursor` API and DrissionPage compatibility.
- [ ] Create a prototype script testing `humancursor` with a raw `DrissionPage` session.

**Plans:** 2 plans
- [ ] 01-01-PLAN.md — Refactor mouse.py to use humancursor library and implement core movement loop.
- [ ] 01-02-PLAN.md — Create trajectory comparison prototype for visual validation.

## Phase 2: Implementation (Refactor)
- [ ] Implement `DrissionPageCursorAdapter` to bridge `humancursor` and DrissionPage.
- [ ] Refactor `src/hcaptcha_challenger/agent/mouse.py` to use `humancursor`.
- [ ] Update `src/hcaptcha_challenger/agent/robotic.py` to utilize the new `mouse.py` API.
- [ ] Align `AgentConfig` and `mouse_config.py` with `humancursor` settings.

## Phase 3: Verification & Cleanup
- [ ] Add new test case `tests/test_agent_mouse_movement.py` to verify trajectory properties.
- [ ] Perform visual verification using `examples/demo_drissionpage.py`.
- [ ] Remove all dead code and inlined easing/bezier functions from `mouse.py`.
- [ ] Final integration test with a live hCaptcha challenge.
