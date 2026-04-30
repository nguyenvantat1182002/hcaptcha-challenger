# hcaptcha-challenger

## What This Is

`hcaptcha-challenger` is a Python automation toolkit for solving hCaptcha challenges through browser orchestration, typed challenge models, and LLM-assisted reasoning. It is used by both internal developers/test engineers and automation-focused users who need stable captcha-solving workflows. This milestone focuses on replacing the current human-like cursor movement implementation with behavior aligned to the HumanCursor style.

## Core Value

The solver reliably completes hCaptcha challenge interactions with realistic, consistent cursor motion while preserving existing integration stability.

## Requirements

### Validated

- ✓ CLI-driven challenge solving and dataset workflows are available through `hc` commands — existing
- ✓ Browser-driven challenge orchestration is implemented via `AgentV` and `RoboticArm` — existing
- ✓ Typed challenge models and provider-backed reasoning pipeline are integrated and operational — existing
- ✓ Runtime configuration via environment-backed `AgentConfig` and `.env` support is in place — existing

### Active

- [ ] Replace the current cursor movement core algorithm with a HumanCursor-style movement profile.
- [ ] Keep existing public API behavior as default compatibility path; only add API extensions where strictly necessary.
- [ ] Support HumanCursor-style motion behavior in web automation paths.
- [ ] Define and enforce quantitative motion-parity benchmarks versus the target HumanCursor-style profile.
- [ ] Preserve existing test compatibility and pass baseline regression checks after migration.

### Out of Scope

- System/native desktop cursor automation parity in this phase — web cursor behavior is the immediate scope.
- Expanding anti-bot evasion goals beyond realistic motion behavior for testing and solver stability — risk and ethics boundary.
- Unrelated solver architecture rewrites (providers, challenge classifiers, or CLI redesign) — not needed for the cursor migration goal.

## Context

- The current codebase is a brownfield Python project using Typer CLI, Pydantic models/settings, DrissionPage/Playwright browser automation, and provider adapters for multimodal reasoning.
- Cursor movement logic is currently part of orchestration behavior in the agent layer and must be upgraded without destabilizing challenge lifecycle flow.
- Existing codebase mapping artifacts (`.planning/codebase/*.md`) provide architecture, conventions, and concern baselines to guide implementation and planning.
- The target reference for motion behavior is the HumanCursor approach from riflosnake/HumanCursor.

## Constraints

- **Compatibility**: Existing public interfaces should remain stable by default — avoid breaking consumers.
- **Scope**: Primary implementation target is web automation cursor behavior — aligns with selected scope.
- **Quality**: Migration must keep existing tests green and include measurable movement profile validation.
- **Process**: Work proceeds in interactive GSD mode with documented planning artifacts committed to git.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Interactive workflow mode | User wants review gates through planning flow | — Pending |
| Prioritize API compatibility over API redesign | User selected compatibility-first when A/B conflicted | — Pending |
| Include research, plan-check, and verifier agents | Higher quality planning/execution for non-trivial migration | — Pending |
| Target HumanCursor-style behavior as migration reference | Explicit product requirement for cursor algorithm replacement | — Pending |
| Focus this milestone on web cursor path | User selected web scope and did not prioritize system cursor in this run | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-30 after initialization*
