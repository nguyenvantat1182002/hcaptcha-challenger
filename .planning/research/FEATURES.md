# Feature Research

**Domain:** HumanCursor-style cursor movement module for browser automation
**Researched:** 2026-04-30
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Curved, non-linear trajectory generation | HumanCursor/ghost-cursor baseline behavior uses Bezier-like curves rather than straight-line teleport or linear interpolation | MEDIUM | Must emit dense `mousemove` sequences over realistic paths; align with existing `generate_human_trajectory` integration in `agent/mouse.py` |
| Human-like velocity profile (accelerate-mid-decelerate) | Constant-speed movement is a common bot tell; modern cursor libs model easing/Fitts-like timing | MEDIUM | Keep per-point delay variability and distance-aware timing; configurable via `HumanConfig` |
| Randomized in-element target point selection | Clicking exact element center every time is robotic and widely avoided in established libs | LOW | Reuse random hitbox targeting with bounded ranges; preserve deterministic test mode option |
| Action parity for move/click/drag/scroll | HumanCursor-style modules are expected to cover complete pointer interaction lifecycle, not just move | MEDIUM | Required to match existing solver paths (`RoboticArm`) and avoid partial migration regressions |
| Configurable behavior presets with safe defaults | Users expect compatibility-first migration with optional realism tuning | LOW | Keep default backward-compatible profile; expose careful/aggressive presets through existing config surface |
| Debug visibility and telemetry hooks | Teams need to inspect path realism and tune failed interactions in CI/local runs | MEDIUM | Support trace hooks (path points, delays, overshoot flags), with optional visible cursor marker in debug-only mode |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Quantitative motion-parity benchmarking against HumanCursor profile | Turns "looks human" into measurable acceptance criteria for migration and regression gates | HIGH | Compute metrics like path curvature, speed variance, pause distribution, overshoot frequency; wire into test suite |
| Adaptive motion strategy by interaction context | Better solve reliability by changing motion style for checkbox clicks, tile selection, drag gestures, and dense targets | HIGH | Strategy selector in orchestration layer chooses profile parameters per action type and target geometry |
| Session-level behavior coherence | Prevents per-action randomness from becoming statistically inconsistent across a full challenge session | MEDIUM | Maintain session seed/behavior envelope (tempo band, hesitation profile) while preserving action-level variation |
| Failure-aware re-aim/recover loop | Improves robustness on small/animated targets without brittle retries | MEDIUM | Add micro-correction and second-pass targeting logic when miss likelihood is high or DOM shifts before click |
| Cross-driver abstraction (DrissionPage + Playwright) with identical motion semantics | Unique portability for mixed automation stacks in one project | HIGH | Keep shared trajectory core, thin driver adapters; avoids duplicate algorithm logic per backend |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| "Maximum stealth mode" claims or anti-detection guarantees | Stakeholders want certainty against bot systems | Overpromises, creates legal/ethical risk, and quickly goes stale as detection changes | Position module as realism/stability layer; ship measurable behavior quality metrics instead of bypass claims |
| Excessive randomization on every parameter | Teams assume more randomness equals more human-like | Produces incoherent motion signatures, flaky clicks, and harder debugging | Use bounded distributions plus session-level coherence and profile presets |
| Full system cursor parity in this migration phase | Seems like future-proofing | Expands scope beyond current web-only milestone and delays core delivery | Keep web cursor focus now; track system cursor as later phase if needed |
| Replacing orchestration architecture during movement migration | Desire to "clean up everything at once" | High regression risk across solver pipeline; violates compatibility-first requirement | Isolate movement core replacement behind existing APIs and config interfaces |

## Feature Dependencies

```text
Curved trajectory generation
    └──requires──> Driver event adapter (mousemove/down/up/wheel contract)
                         └──requires──> Current API compatibility layer

Velocity profile + timing variance
    └──requires──> Configurable delay model
                         └──requires──> Preset/override configuration surface

Random in-element targeting
    └──requires──> Reliable element geometry extraction

Drag/scroll parity
    └──requires──> Move/click primitives

Motion-parity benchmarking
    └──requires──> Telemetry hooks
                         └──requires──> Stable trajectory data schema

Adaptive context strategy ──enhances──> Core trajectory generation
Session-level coherence ──enhances──> Velocity + targeting realism

Excessive randomization ──conflicts──> Session-level behavior coherence
"Stealth guarantee" messaging ──conflicts──> Compatibility-first quality positioning
```

### Dependency Notes

- **Curved trajectory generation requires driver event adapter:** The math layer is only useful if browser backends execute full event sequences consistently.
- **Velocity profile requires config surface:** Distance-aware and profile-aware timing must be externally tunable to keep API compatibility while enabling migration.
- **Motion-parity benchmarking requires telemetry hooks:** You cannot enforce parity thresholds without capturing path/timing/overshoot outputs in a stable format.
- **Adaptive strategy enhances core trajectory generation:** Strategy selection should tune core parameters, not fork a second movement engine.
- **Excessive randomization conflicts with session coherence:** Independent random knobs per action create implausible behavior drift and brittle tests.

## MVP Definition

### Launch With (v1)

Minimum viable product - what's needed to validate the concept.

- [ ] Curved trajectory + variable velocity movement engine - core HumanCursor-style parity requirement
- [ ] Move/click/drag/scroll action parity in browser paths - preserves existing solver workflows
- [ ] Config presets and compatibility-safe defaults - avoids breaking current consumers
- [ ] Basic telemetry for trajectory/timing validation - enables quantitative parity checks

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Adaptive context strategy - add when baseline parity and regressions are stable
- [ ] Failure-aware re-aim/recover loop - add when miss/error telemetry identifies high-value cases
- [ ] Session-level coherence controls - add when multiple-session metric drift appears in benchmarks

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Cross-driver motion SDK packaging - defer until Playwright/DrissionPage parity is proven in production
- [ ] System cursor support parity - defer due to current web-only milestone scope

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Curved trajectory + velocity profile | HIGH | MEDIUM | P1 |
| Action parity (move/click/drag/scroll) | HIGH | MEDIUM | P1 |
| Config presets + compatibility defaults | HIGH | LOW | P1 |
| Telemetry + parity metrics baseline | HIGH | MEDIUM | P1 |
| Adaptive context strategy | MEDIUM | HIGH | P2 |
| Failure-aware re-aim/recover | MEDIUM | MEDIUM | P2 |
| Session-level coherence | MEDIUM | MEDIUM | P2 |
| System cursor parity | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | HumanCursor (riflosnake) | ghost-cursor (Xetera) | Our Approach |
|---------|---------------------------|------------------------|--------------|
| Curved trajectory | Natural motion with curvature/acceleration | Bezier path generation | Keep HumanCursor-style core with existing Python integration |
| Target selection | Relative in-element positioning | Random in-element destination | Bounded random targeting tuned for solver task geometry |
| Overshoot/readjust | Present in ecosystem variants | Explicit overshoot threshold + readjust behavior | Add as configurable behavior tied to distance/target size |
| Debuggability | Basic demos/helpers | Optional visible cursor + options | Add first-class telemetry for parity validation and CI diagnostics |
| Scope fit | Selenium/web + system cursor modes | Puppeteer-focused | Web-first for current milestone, system mode deferred |

## Sources

- [PROJECT.md context](../PROJECT.md) (HIGH confidence - first-party project constraints)
- [Codebase architecture context](../codebase/ARCHITECTURE.md) (HIGH confidence - first-party architecture)
- [Playwright Mouse API](https://playwright.dev/docs/api/class-mouse) (HIGH confidence - official docs)
- [HumanCursor README (riflosnake)](https://raw.githubusercontent.com/riflosnake/HumanCursor/main/README.md) (HIGH confidence - upstream reference)
- [ghost-cursor README (Xetera)](https://raw.githubusercontent.com/Xetera/ghost-cursor/master/README.md) (HIGH confidence - established ecosystem implementation)
- [humancursor-playwright package](https://pypi.org/project/humancursor-playwright/) (MEDIUM confidence - package metadata and examples)
- [Behavioral fingerprinting reference (Pydoll)](https://pydoll.tech/docs/deep-dive/fingerprinting/behavioral-fingerprinting/) (MEDIUM confidence - non-official but technically aligned analysis)

---
*Feature research for: HumanCursor-style browser motion migration*
*Researched: 2026-04-30*
