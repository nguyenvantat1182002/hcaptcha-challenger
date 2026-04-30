# Project Research Summary

**Project:** hcaptcha-challenger
**Domain:** HumanCursor-style web cursor motion migration for Python hCaptcha automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project is a brownfield migration effort: replace the current cursor movement core with HumanCursor-style behavior while preserving existing solver APIs and challenge orchestration. Expert implementations in this space consistently use a layered design: orchestration decides intent, a dedicated movement engine synthesizes trajectories and timing, and a browser adapter emits low-level events. The strongest recommendation is to keep the migration compatibility-first with a facade boundary and feature flag, not a big-bang replacement inside `RoboticArm`.

The recommended technical approach is Playwright-native event emission backed by internal NumPy/SciPy trajectory synthesis, typed profile configuration, and deterministic seed controls for regression reproducibility. Feature priority is clear: launch with curved trajectory + variable velocity, full pointer action parity (move/click/drag/scroll), compatibility-safe presets, and telemetry needed to prove parity quantitatively.

The largest risks are semantic regressions (event order and hover/click cadence), stale coordinate targeting in dynamic pages, and throughput collapse if high-fidelity movement is applied to all interactions. Mitigation should be phase-gated: baseline first, adapter boundary second, contract tests third, then selective-realism rollout with explicit SLO/cost controls.

## Key Findings

### Recommended Stack

Research supports a pragmatic, maintainable stack centered on browser-native control and testable numerics. The stack choices align with current project conventions and avoid stale or over-scoped dependencies.

**Core technologies:**
- `playwright>=1.45,<2`: browser mouse event emitter (`move/down/up/wheel`) with trace tooling and long-term maintainability.
- `numpy>=2.0,<3`: fast vector math and seeded RNG for controlled realism plus deterministic replay in tests.
- `scipy>=1.13,<2`: interpolation primitives (`splprep/splev` or spline alternatives) and statistical parity checks.
- `pydantic>=2.7,<3` + `pydantic-settings>=2.3,<3`: typed movement profile configuration consistent with existing project patterns.
- `pytest` / `pytest-asyncio` (existing): regression and parity gate enforcement.

Critical version constraints from research:
- Keep `playwright>=1.45,<2` with Python `>=3.10`.
- Pin tested NumPy/SciPy pairs in lockfile and validate in CI.
- Avoid direct reliance on `HumanCursor`/`humancursor-playwright` as long-term production core.

### Expected Features

Feature research is strongly aligned around compatibility-first launch criteria, with clear differentiation and defer buckets.

**Must have (table stakes):**
- Curved, non-linear trajectories with human-like velocity envelope.
- Pointer lifecycle parity: move, click, drag, and scroll behaviors.
- Randomized in-element target selection with bounded distributions.
- Configurable presets and safe defaults preserving current behavior.
- Telemetry hooks for path/timing/overshoot diagnostics and parity validation.

**Should have (competitive):**
- Quantitative motion-parity benchmarking suite.
- Adaptive strategy by interaction context (checkbox vs tile vs drag).
- Session-level behavior coherence controls.
- Failure-aware re-aim/recover loop for small or shifting targets.

**Defer (v2+):**
- Cross-driver SDK packaging beyond immediate migration need.
- System/native desktop cursor parity (explicitly out of current scope).

### Architecture Approach

Architecture research recommends strict boundary control: keep `RoboticArm` responsible for action intent, introduce `CursorMotionFacade` as migration seam, implement `HumanMotionEngine` as a composable synthesis pipeline, and isolate browser specifics inside a cursor adapter contract. This allows legacy/human dual-path rollout with low blast radius, contract tests at layer boundaries, and telemetry-driven rollout decisions instead of visual-only validation.

**Major components:**
1. `RoboticArm` — chooses interaction intent and target.
2. `CursorMotionFacade` — compatibility boundary and feature-flag switch.
3. `HumanMotionEngine` — control points, curve sampling, distortion, timing.
4. `MotionProfile`/RNG policy — typed behavior knobs and reproducibility.
5. `BrowserCursorAdapter` — executes timed point streams in backend-specific APIs.
6. `MotionTelemetry` — emits metrics for parity, reliability, and rollout gating.

### Critical Pitfalls

1. **No baseline before swap** — capture movement/event/outcome baselines first and gate on no-regression thresholds.
2. **Assuming native interpolation is enough** — implement explicit profile layers for non-linear timing, jitter, overshoot, and dwell behavior.
3. **Breaking interaction semantics** — enforce move/hover/down/up/click and drag/scroll contracts in CI.
4. **Coordinate drift on dynamic UI** — revalidate geometry immediately pre-click; replan when layout/viewport shifts.
5. **Throughput collapse from realism everywhere** — adopt selective realism policy and monitor solve-time/cost SLOs.

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 0: Migration Safety Boundaries
**Rationale:** Brownfield stability requires interface boundaries before algorithm changes.
**Delivers:** `CursorMotionFacade` contract, adapter extraction, legacy path preservation as default.
**Addresses:** Compatibility-first requirement and anti-feature of orchestration rewrites.
**Avoids:** Fragile orchestration coupling and big-bang cutover risk.

### Phase 1: Baseline & Parity Benchmarking
**Rationale:** Quantitative baseline is mandatory to judge migration success.
**Delivers:** Movement/event/outcome baseline capture, telemetry schema, parity gate definitions.
**Addresses:** Table-stake telemetry and differentiator-ready benchmarking foundation.
**Avoids:** "Looks human but regressed outcomes" failure mode.

### Phase 2: Human Motion Engine Core
**Rationale:** Core behavior should land behind stable boundaries with deterministic controls.
**Delivers:** Curved trajectory synthesis, variable velocity model, bounded target randomization, profile presets.
**Uses:** Playwright + NumPy + SciPy + Pydantic stack.
**Implements:** `HumanMotionEngine` + `MotionProfile` + RNG policy pipeline.
**Avoids:** Linear interpolation-only behavior and unseeded randomness drift.

### Phase 3: Interaction Contract Integration
**Rationale:** End-user reliability depends on full semantic parity, not coordinate parity.
**Delivers:** move/hover/click/drag/scroll contract tests, adapter behavior verification on supported backends.
**Addresses:** Table-stake action lifecycle parity.
**Avoids:** Subtle widget regressions and flaky challenge interactions.

### Phase 4: Progressive Rollout & Performance Policy
**Rationale:** Human-like movement must not break throughput economics.
**Delivers:** Feature-flag rollout plan, selective realism profiles (strict/balanced/fast), SLO instrumentation.
**Addresses:** Stability and scalability under production load.
**Avoids:** Solve-time and cost blowups from indiscriminate high-fidelity movement.

### Phase 5: End-to-End Validation of Layered Signals
**Rationale:** Cursor realism is one signal among many in challenge outcomes.
**Delivers:** Validation protocol correlating cursor metrics with pass rates alongside non-cursor controls.
**Addresses:** Scope realism and honest success criteria.
**Avoids:** Over-claiming anti-bot completeness from movement work alone.

### Phase Ordering Rationale

- Order follows dependency chain: boundaries -> baseline -> engine -> semantic integration -> rollout -> full validation.
- Grouping mirrors architecture seams, reducing regression blast radius during each phase.
- Risk-heavy concerns from pitfalls are pulled forward (baseline and boundary isolation) instead of deferred.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Contract Integration):** backend-specific event semantics and edge-case parity matrix may need targeted API/behavior deep-dive.
- **Phase 5 (E2E Layered Validation):** multi-signal outcome attribution needs sharper measurement design to avoid false conclusions.

Phases with standard patterns (can usually skip research-phase):
- **Phase 0 (Safety Boundaries):** facade/adapter extraction in brownfield Python systems is well-established.
- **Phase 1 (Baseline/Telemetry):** benchmarking and regression-gate setup is standard and well documented.
- **Phase 2 (Motion Engine Core):** established curve/timing synthesis patterns with clear library support.
- **Phase 4 (Rollout/Performance):** feature-flag canary and SLO tuning patterns are mature.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Anchored in official Playwright/SciPy docs and clear project fit; version constraints are explicit. |
| Features | HIGH | Strongly aligned with project constraints plus established HumanCursor/ghost-cursor expectations. |
| Architecture | MEDIUM | Pattern quality is strong, but internal implementation details remain to be validated against live code touchpoints. |
| Pitfalls | MEDIUM-HIGH | Risks are realistic and actionable; some secondary sources are community-grade and need empirical confirmation. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Backend behavior matrix depth:** DrissionPage vs Playwright edge-case parity still needs execution-time validation.
- **Quantitative thresholds:** exact pass/fail numbers for parity and SLO gates must be calibrated from real baseline data.
- **Session coherence tuning:** optimal randomness envelopes are not pre-resolved and require iterative benchmark-driven tuning.
- **Attribution limits:** improved cursor realism may not materially move solve rates in all environments; validate against non-cursor factors.

## Sources

### Primary (HIGH confidence)
- https://playwright.dev/python/docs/api/class-mouse — mouse primitives and interpolation semantics.
- https://playwright.dev/python/docs/input — browser input interaction behavior.
- https://docs.scipy.org/doc/scipy/reference/interpolate.html — interpolation APIs for trajectory synthesis.
- https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event — event semantics reference.
- `../PROJECT.md` and `../codebase/ARCHITECTURE.md` — first-party constraints and architecture baseline.

### Secondary (MEDIUM confidence)
- https://pypi.org/project/HumanCursor/ — reference package scope and recency.
- https://pypi.org/project/humancursor-playwright/ — adaptation maturity signals.
- https://raw.githubusercontent.com/riflosnake/HumanCursor/main/README.md — movement model expectations.
- https://raw.githubusercontent.com/Xetera/ghost-cursor/master/README.md — ecosystem baseline behavior.
- https://raw.githubusercontent.com/patrikoss/pyclick/master/pyclick/humancurve.py — implementation pattern reference.

### Tertiary (LOW-MEDIUM confidence)
- https://bytetunnels.com/posts/browser-automation-human-like-mouse-movement/ — community movement guidance.
- https://substack.thewebscraping.club/p/bypass-datadome-mouse-movements-in-playwright — practitioner heuristics.
- https://www.zenrows.com/blog/humancursor — vendor-style discussion, useful but not authoritative.

---
*Research completed: 2026-04-30*
*Ready for roadmap: yes*
