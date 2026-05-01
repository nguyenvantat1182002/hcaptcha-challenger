# Roadmap: HumanCursor Integration

## Phase 1: Foundation & Dependencies
**Goal:** Establish the technical foundation by installing required dependencies and verifying the environment readiness for HumanCursor integration.
**Plans:** 1 plan
- [x] 01-01-PLAN.md — Environment Verification

**Requirements:** 1.1, 1.2

## Phase 2: Implementation & Adaptation
**Goal:** Replace legacy Bezier movement with `humancursor` and refactor configuration.
**Plans:** 2 plans
- [x] 02-01-PLAN.md — Mouse Logic Refactor
- [x] 02-02-PLAN.md — Integration & Demo

**Requirements:** PH2-ADP, PH2-CFG, PH2-CLN

## Phase 3: Fine-tuning & Optimization
**Goal:** Calibrate movement parameters and introduce behavioral variety to bypass detection.
**Plans:** 2 plans
- [ ] 03-01-PLAN.md — Persona System & Refined Presets
- [ ] 03-02-PLAN.md — Integration & Calibration Logic

**Requirements:** PH3-PER, PH3-DEL, PH3-TEL

## Phase 4: Verification & Cleanup
- **Task 4.1: Implementation Testing.** Run full integration tests with real hCaptcha challenges.
- **Task 4.2: Code Cleanup.** Remove any remaining unused legacy constants.
- **Task 4.3: Documentation Update.** Update internal docs or comments to reflect the change to `HumanCursor`.
