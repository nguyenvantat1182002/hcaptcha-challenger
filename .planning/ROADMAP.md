# Roadmap: hcaptcha-challenger

## Overview

This roadmap migrates web cursor behavior to a HumanCursor-style profile without breaking existing integrations. Work is sequenced to preserve compatibility first, then ship motion realism, then guarantee action semantics, and finally enforce quantitative parity gates with regression-safe validation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Compatibility Baseline** - Keep default API compatibility while establishing baseline motion telemetry.
- [ ] **Phase 2: Human Motion Core** - Deliver curved trajectories, velocity shaping, and configurable HumanCursor-style profiles.
- [ ] **Phase 3: Action Semantics Parity** - Apply HumanCursor-style behavior consistently across move/click/drag/scroll actions.
- [ ] **Phase 4: Parity Gates & Validation** - Enforce measurable parity thresholds with post-migration telemetry and CI checks.

## Phase Details

### Phase 1: Compatibility Baseline
**Goal**: Users keep existing default behavior while baseline cursor telemetry is captured for migration comparison.
**Depends on**: Nothing (first phase)
**Requirements**: COMP-01, TELE-01
**Success Criteria** (what must be TRUE):
  1. Existing automation call paths continue to work without code changes when users do not opt into new motion behavior.
  2. Users can capture pre-migration cursor telemetry in a repeatable schema for web challenge interactions.
  3. Users can run baseline capture without destabilizing normal challenge solve workflows.
**Plans**: TBD

### Phase 2: Human Motion Core
**Goal**: Users can opt into HumanCursor-style movement profiles with realistic trajectories and stable configuration presets.
**Depends on**: Phase 1
**Requirements**: MOTN-01, MOTN-02, MOTN-03, COMP-02, COMP-04
**Success Criteria** (what must be TRUE):
  1. Users who enable HumanCursor mode get curved, non-linear cursor paths during web interactions.
  2. Users observe non-constant velocity behavior (acceleration, in-flight variation, deceleration) during movement.
  3. Users get bounded randomized in-element click targets instead of fixed destination points.
  4. Users can explicitly enable HumanCursor-style behavior through configuration while legacy default remains unchanged.
  5. Users can choose safe realism presets that balance motion quality and stability.
**Plans**: TBD

### Phase 3: Action Semantics Parity
**Goal**: Users get HumanCursor-style behavior parity across all core pointer actions in web automation.
**Depends on**: Phase 2
**Requirements**: ACTN-01, ACTN-02, ACTN-03, ACTN-04
**Success Criteria** (what must be TRUE):
  1. Users get HumanCursor-style movement parity for pointer move actions in challenge workflows.
  2. Users get HumanCursor-style click behavior parity, including realistic approach-to-click motion.
  3. Users get HumanCursor-style drag behavior parity for drag-based challenge interactions.
  4. Users get HumanCursor-style scroll behavior parity in relevant page interaction paths.
**Plans**: TBD

### Phase 4: Parity Gates & Validation
**Goal**: Users can quantitatively verify post-migration behavior and enforce parity thresholds in automated validation.
**Depends on**: Phase 3
**Requirements**: TELE-02, TELE-03, BENC-01, BENC-02, BENC-03, BENC-04, COMP-03
**Success Criteria** (what must be TRUE):
  1. Users can capture post-migration telemetry in the same schema as baseline and compare results directly.
  2. Users can inspect trajectory and timing diagnostics to identify and debug movement regressions.
  3. Users have measurable parity metrics for curvature, velocity variance/pause distribution, and overshoot/readjust envelope.
  4. Users can run deterministic movement mode for reproducible tests and metric comparisons.
  5. Users can enforce pass/fail parity thresholds in test and CI workflows.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 2 -> 2.1 -> 2.2 -> 3 -> 3.1 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Compatibility Baseline | 0/0 | Not started | - |
| 2. Human Motion Core | 0/0 | Not started | - |
| 3. Action Semantics Parity | 0/0 | Not started | - |
| 4. Parity Gates & Validation | 0/0 | Not started | - |
