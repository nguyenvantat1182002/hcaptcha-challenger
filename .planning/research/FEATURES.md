# Feature Research

**Domain:** Realistic cursor movement engine for browser automation (HumanCursor-style migration)
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Curved, non-linear trajectory generation | Direct `move/click` APIs are linear/robotic by default; human-like tools consistently use curved paths | MEDIUM | Bezier/spline trajectory with per-move randomness; must keep current click outcomes stable |
| Variable velocity profile (accel/decel) | Constant-speed motion is visibly synthetic; Fitts-law style timing is common in HumanCursor/ghost-cursor ecosystems | MEDIUM | Implement easing-based timing tied to distance/target size rather than fixed delay |
| Randomized in-element target point selection | Clicking exact center every time is a bot signal and breaks realism | LOW | Keep within safe padding so hCaptcha tiles/buttons are still reliably hit |
| Human-like click cadence (aim delay + hold duration) | Realistic motion without realistic click timing still looks scripted | LOW | Configurable pre-click hesitation and down/up hold window |
| Drag-and-drop path realism | This project uses drag challenges; movement realism must include hold-drag-release path behavior | MEDIUM | Reuse same path engine for drag with short pause before down and after drop |
| Iframe/viewport coordinate correctness | hCaptcha lives inside nested frames; realistic engine is useless if coordinates drift | HIGH | Maintain existing frame-offset mapping semantics in `DrissionPageMouse` adapter |
| Backward-compatible integration surface | Existing automation flow must not break during migration | HIGH | Keep existing `RoboticArm` behavior as default path; add opt-in params only when needed |
| Debug visibility for path validation | Teams need to verify movement parity and troubleshoot misses | LOW | Preserve visual/debug trace support and optional point logging for benchmarks |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Quantitative motion-parity benchmarking against HumanCursor-style profile | Turns "looks human" into measurable acceptance criteria for migration sign-off | MEDIUM | Compare curvature, speed distribution, click offset entropy, and drag smoothness |
| Adaptive movement mode by action risk (checkbox vs tile vs drag) | Improves solve reliability by using precision where needed and naturalness elsewhere | MEDIUM | Policy layer selects parameter preset per action type/distance |
| Deterministic replay mode with seed capture | Enables flaky-test debugging while preserving stochastic production behavior | MEDIUM | Record RNG seed + generated waypoints for exact re-run in CI/debug |
| Calibration profile system (`default`, `careful`, custom overrides) | Supports different environments without code forks | LOW | Extend current preset model and expose safe override boundaries |
| Safety guardrails for target-zone confidence | Reduces accidental misses from over-randomized trajectories | MEDIUM | Clamp endpoint selection and fallback to steady mode for tiny targets |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Always-on maximum randomness | "More random means more human" intuition | Produces unstable clicks/drags and regression noise; hurts solve rate | Bounded stochastic ranges + action-specific presets |
| Full desktop/system cursor parity in this migration | Desire for one universal cursor engine | Out of scope for current milestone; increases OS-specific complexity and risk | Keep web-path parity first; evaluate system cursor in a separate phase |
| Public API redesign during movement migration | Chance to "clean up interfaces" | Breaks compatibility and delays delivery | Preserve current API; introduce additive optional config only |
| Hard anti-bot bypass claims in feature contract | Marketing pressure for stealth guarantees | Unverifiable and ethically risky; behavior changes on target sites | Frame goal as realistic interaction + solver stability, not evasion guarantees |

## Feature Dependencies

```text
Curved trajectory generation
    └──requires──> Coordinate normalization (iframe/local/global mapping)
                         └──requires──> Existing DrissionPage adapter compatibility

Variable velocity profile
    └──enhances──> Curved trajectory generation

Random in-element target selection
    └──requires──> Safety guardrails for hit-zone bounds

Human-like click cadence
    └──requires──> Random in-element target selection

Drag-and-drop realism
    └──requires──> Curved trajectory generation
    └──requires──> Variable velocity profile

Motion-parity benchmarks
    └──requires──> Debug visibility for path traces
    └──requires──> Deterministic replay mode

Always-on maximum randomness ──conflicts──> Solver reliability baseline
API redesign during migration ──conflicts──> Backward-compatible integration surface
```

### Dependency Notes

- **Curved trajectory generation requires coordinate normalization:** path quality is irrelevant if the endpoint mapping is wrong inside challenge iframes.
- **Variable velocity profile enhances curved trajectory generation:** shape-only realism without timing realism still appears scripted.
- **Random in-element target selection requires safety guardrails:** randomness must stay within reliable click zones for captcha tiles/buttons.
- **Motion-parity benchmarks require debug visibility and deterministic replay:** benchmark failures must be reproducible to tune parameters.
- **API redesign conflicts with compatibility goals:** migration success criteria explicitly prioritize stable consumer-facing behavior.

## MVP Definition

### Launch With (v1)

Minimum viable product for this migration phase.

- [ ] Curved trajectory generation with bounded jitter — core HumanCursor-style behavior replacement
- [ ] Variable velocity + click cadence — removes robotic timing signatures while preserving interaction reliability
- [ ] Random in-element click target selection with guardrails — realistic but safe hit selection
- [ ] Drag-and-drop path realism — required for existing drag challenge flow
- [ ] Backward-compatible `RoboticArm` integration — no breaking API changes
- [ ] Basic debug trace + motion benchmark checks — enforce parity and prevent regressions

### Add After Validation (v1.x)

Features to add once core migration is stable in regression suites.

- [ ] Adaptive per-action movement mode — add once baseline solve-rate parity is proven
- [ ] Deterministic replay mode — add when tuning/CI flake triage becomes a bottleneck
- [ ] Expanded preset library — add after collecting run data from real challenge distributions

### Future Consideration (v2+)

Features to defer until cursor migration goal is fully achieved.

- [ ] System/desktop cursor unification — separate scope with OS-level constraints
- [ ] Advanced learned movement models (record/replay from human telemetry) — high complexity, unclear ROI until current parity is validated

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Curved trajectory + variable velocity | HIGH | MEDIUM | P1 |
| Random in-element targets + click cadence | HIGH | LOW | P1 |
| Drag-and-drop realism | HIGH | MEDIUM | P1 |
| Compatibility-preserving integration | HIGH | HIGH | P1 |
| Motion-parity benchmarks | HIGH | MEDIUM | P1 |
| Adaptive per-action mode | MEDIUM | MEDIUM | P2 |
| Deterministic replay mode | MEDIUM | MEDIUM | P2 |
| Expanded preset profiles | MEDIUM | LOW | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | HumanCursor (Python) | ghost-cursor (Puppeteer) | Our Approach |
|---------|-----------------------|--------------------------|--------------|
| Curved movement + variable speed | Natural motion with curvature/acceleration | Bezier + distance-aware speed | Keep current in-repo human path engine and tune for parity |
| Random target point selection | Supports relative target positions | Random point inside element | Bounded random in-element targeting with captcha-safe zones |
| Overshoot/correction style behavior | Exposed via natural motion behavior and params | Explicit overshoot threshold behavior | Optional bounded overshoot only where it does not hurt hit reliability |
| Integration with existing flow | Selenium-centric APIs | Puppeteer-centric APIs | Native to current `RoboticArm` + DrissionPage adapter flow |

## Sources

- [Playwright Mouse API](https://playwright.dev/docs/api/class-mouse) (official docs, retrieved 2026-04-30, MEDIUM confidence for baseline mouse semantics)
- [HumanCursor PyPI](https://pypi.org/project/HumanCursor/) (official package metadata/readme, retrieved 2026-04-30, MEDIUM confidence)
- [ghost-cursor npm](https://www.npmjs.com/package/ghost-cursor) (official package docs, retrieved 2026-04-30, MEDIUM confidence)
- [ByteTunnels: Browser Automation with Human-Like Mouse Movement](https://bytetunnels.com/posts/browser-automation-human-like-mouse-movement/) (community implementation analysis, retrieved 2026-04-30, LOW confidence unless cross-verified)

---
*Feature research for: HumanCursor-style cursor movement migration in hcaptcha-challenger*
*Researched: 2026-04-30*
# Feature Research

**Domain:** HumanCursor-style cursor engine for web automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Curved non-linear paths | Core "human-like" expectation | MEDIUM | Needs trajectory generator with anchor variation. |
| Variable speed/acceleration | Basic realism signal | MEDIUM | Implement via profile-based velocity envelope. |
| Deterministic debug mode | Required for regression/testing | LOW | Seed-based reproducibility for CI and diffs. |
| Existing API compatibility | Brownfield integration safety | MEDIUM | Keep current call sites unchanged by default. |
| Click/drag path consistency | End-to-end interaction fidelity | MEDIUM | Same profile engine for move, click approach, drag segments. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Benchmark parity scoring against reference | Objective migration quality gate | HIGH | Compare curvature, velocity, dwell, jitter envelopes. |
| Profile presets (`steady`, `agile`, `natural`) | Better tuning for challenge variants | MEDIUM | Config-driven with strict schema validation. |
| Adaptive path retry shaping | Robustness on missed targets | HIGH | Adjust approach profile on failures. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Unbounded random jitter | Looks "more human" at first glance | Breaks repeatability and harms click accuracy | Seeded bounded perturbations with max deviation caps. |
| Full API rewrite immediately | Cleaner abstraction fantasy | High migration risk and downstream breakage | Compatibility-first adapter + gradual API extension. |

## Feature Dependencies

```text
Benchmark parity scoring
    └──requires──> deterministic debug mode
                       └──requires──> profile schema stability

Adaptive retry shaping ──enhances──> curved non-linear paths

API rewrite now ──conflicts──> compatibility-first migration
```

### Dependency Notes

- **Parity scoring requires deterministic mode:** Without reproducibility, benchmark drift is untriageable.
- **Retry shaping enhances trajectory realism:** Useful only after base path engine is stable.
- **Immediate rewrite conflicts with compatibility:** It violates the selected migration priority.

## MVP Definition

### Launch With (v1)

- [ ] HumanCursor-style path/velocity engine in web flow — core migration goal.
- [ ] Backward-compatible default behavior via existing API surface — prevents integration breakage.
- [ ] Benchmark + regression suite for motion parity and correctness — defines "done" objectively.

### Add After Validation (v1.x)

- [ ] Additional profile presets with tuning knobs — after baseline parity is stable.
- [ ] Rich diagnostics/visual overlays for path analysis — when debugging needs increase.

### Future Consideration (v2+)

- [ ] Native/system cursor automation parity — deferred by current scope choice.
- [ ] Automatic anti-bot strategy exploration — deferred due risk boundary.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| HumanCursor-style core movement | HIGH | HIGH | P1 |
| Compatibility-first adapter | HIGH | MEDIUM | P1 |
| Parity benchmark suite | HIGH | MEDIUM | P1 |
| Profile presets expansion | MEDIUM | MEDIUM | P2 |
| Native cursor support | MEDIUM | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Human-like pathing | HumanCursor-style via selenium-oriented utilities | Common bot frameworks often linearize movement | Keep browser-runtime-native implementation with typed configs. |
| Deterministic testing mode | Usually absent or ad-hoc | Often absent | Built-in seeded deterministic mode for CI parity validation. |

## Sources

- Existing architecture/concerns docs in `.planning/codebase/`
- HumanCursor project reference: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor)
- Internal migration goal from `.planning/PROJECT.md`

---
*Feature research for: HumanCursor-style cursor engine*
*Researched: 2026-04-30*
