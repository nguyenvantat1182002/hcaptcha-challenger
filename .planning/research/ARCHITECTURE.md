# Architecture Research

**Domain:** HumanCursor-style movement migration in layered Python hCaptcha solver
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Interface / Orchestration                       │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐   ┌─────────────────────────────────────┐ │
│  │ AgentV (challenge)   │→→ │ RoboticArm (interaction planning)  │ │
│  └──────────────────────┘   └────────────────┬────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                     Movement Engine Boundary                          │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐   ┌─────────────────────────────────────┐ │
│  │ CursorMotionFacade   │→→ │ HumanMotionEngine (path synthesis) │ │
│  └──────────────────────┘   └────────────────┬────────────────────┘ │
│                                ┌──────────────┴──────────────┐       │
│                                │ MotionProfile + RNG policy  │       │
│                                └──────────────────────────────┘       │
├──────────────────────────────────────────────────────────────────────┤
│                       Browser Adapter Boundary                         │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐   ┌─────────────────────────────────────┐ │
│  │ Drission adapter     │   │ Playwright-compatible adapter       │ │
│  └──────────────────────┘   └─────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `RoboticArm` | Decide *what* action to perform (click, drag, hover) and target coordinates | Existing orchestration class remains owner of challenge intent |
| `CursorMotionFacade` | Stable API bridge from orchestration to movement engine; enforces defaults/feature flags | New module in `agent` package exposing sync calls used by `RoboticArm` |
| `HumanMotionEngine` | Compute human-like trajectory points and timing from start/end + profile | Deterministic-by-seed service in `tools` or `agent/motion` subpackage |
| `MotionProfile` | Hold tunable movement parameters (knots, distortion, easing, speed bands) | Typed Pydantic model aligned with existing config conventions |
| `BrowserCursorAdapter` | Execute generated points against browser API without changing solver logic | Driver-specific adapter with a single `move_path(points)` contract |
| `MotionTelemetry` | Capture movement metrics for parity/regression testing | Lightweight logger + structured metrics emitted during movement |

## Recommended Project Structure

```
src/hcaptcha_challenger/
├── agent/
│   ├── robotic.py                    # uses CursorMotionFacade only
│   └── motion/
│       ├── facade.py                 # compatibility bridge + feature flags
│       ├── profiles.py               # MotionProfile typed settings
│       └── telemetry.py              # movement metric capture
├── tools/
│   └── motion/
│       ├── human_engine.py           # trajectory generation pipeline
│       ├── easing.py                 # easing/tween functions
│       └── rng_policy.py             # seeded randomness strategy
├── browser/
│   └── cursor_adapter.py             # driver-specific move/click execution
└── tests/
    ├── test_motion_engine.py
    ├── test_motion_facade.py
    └── test_robotic_motion_integration.py
```

### Structure Rationale

- **`agent/motion/`:** keeps migration boundary close to current `RoboticArm`, minimizing call-site churn and regression risk.
- **`tools/motion/`:** isolates algorithmic concerns from challenge orchestration, preserving layered architecture.
- **`browser/cursor_adapter.py`:** prevents direct driver calls from the engine and allows gradual backend compatibility.
- **`tests/*motion*`:** gives parity and regression suites a clear home, making rollout gates explicit.

## Architectural Patterns

### Pattern 1: Facade + Strategy for Backward Compatibility

**What:** `RoboticArm` calls one facade method; facade selects legacy or human engine based on config/flag.
**When to use:** Brownfield migrations where API compatibility is mandatory.
**Trade-offs:** Slight indirection cost, but significantly lower blast radius.

**Example:**
```python
class CursorMotionFacade:
    def move_to(self, start, end, context):
        if not self.flags.human_cursor_enabled:
            return self.legacy.move_to(start, end)
        path = self.human_engine.build_path(start, end, self.profile, context=context)
        return self.adapter.move_path(path)
```

### Pattern 2: Pipeline Movement Synthesis

**What:** Build path in stages: control points -> curve sampling -> distortion -> timing.
**When to use:** Human-like movement where realism comes from composable transforms.
**Trade-offs:** More components to validate, but easier calibration and testing.

**Example:**
```python
points = generator.control_points(start, end, profile, rng)
curve = generator.sample_curve(points, target_points=profile.target_points)
distorted = generator.apply_distortion(curve, profile.distortion, rng)
timed_path = generator.apply_velocity_model(distorted, profile.easing)
```

### Pattern 3: Contract Tests at Layer Boundaries

**What:** Enforce invariants (start/end preserved, no teleporting, monotonic timestamps) via shared tests.
**When to use:** Replacing core algorithm while preserving behavior expectations.
**Trade-offs:** Upfront test authoring effort, large long-term regression reduction.

## Data Flow

### Request Flow

```
Challenge detected by AgentV
    ↓
RoboticArm resolves interaction target
    ↓
CursorMotionFacade.move_to(start, end, action_context)
    ↓
HumanMotionEngine.build_path(profile, rng_seed)
    ↓
BrowserCursorAdapter.move_path(points_with_timing)
    ↓
Click/drag completion returned to RoboticArm
    ↓
Challenge check response processed by AgentV
```

### State Management

```
AgentConfig / env
    ↓
MotionProfileResolver (default profile + overrides)
    ↓
CursorMotionFacade (immutable profile snapshot per action)
    ↓
HumanMotionEngine (pure-ish computation + seeded RNG)
    ↓
Telemetry sink (stats only, no mutable global coupling)
```

### Key Data Flows

1. **Execution flow:** start/end coordinates + action intent become timed point stream for browser cursor actions.
2. **Configuration flow:** `AgentConfig`/env flags select engine mode and profile variant without changing caller API.
3. **Validation flow:** emitted telemetry is compared against parity thresholds in tests/benchmarks.

## Build Order Implications (Suggested Phase Order)

1. **Define contracts first** (facade API, path point schema, adapter interface).
   - Reason: locks boundaries before algorithm work and prevents spread of migration changes.
2. **Implement dual-path facade** (legacy + human engine switch, default legacy).
   - Reason: enables safe integration tests while behavior remains unchanged by default.
3. **Implement HumanMotionEngine pipeline** behind facade.
   - Reason: algorithm can evolve independently while orchestration remains stable.
4. **Add browser adapter integration** for existing driver path.
   - Reason: isolates driver behavior and keeps algorithm portable.
5. **Add telemetry + parity benchmarks** and regression gates.
   - Reason: quantitative confidence before enabling rollout.
6. **Progressive rollout** (opt-in flag -> canary profile -> default after stability).
   - Reason: minimizes operational regression risk.

## Anti-Patterns

### Anti-Pattern 1: Algorithm Logic Inside `RoboticArm`

**What people do:** Directly insert curve-generation code into orchestration methods.
**Why it's wrong:** Couples challenge workflow with motion internals; hard to test and rollback.
**Do this instead:** Keep `RoboticArm` as orchestrator and route movement through facade.

### Anti-Pattern 2: Unseeded Randomness Everywhere

**What people do:** Call global random functions across multiple layers.
**Why it's wrong:** Non-reproducible failures and unstable tests.
**Do this instead:** Pass a scoped RNG/seed through the engine pipeline and log seed on failure.

### Anti-Pattern 3: Big-Bang Cutover

**What people do:** Replace legacy behavior completely in one release.
**Why it's wrong:** High blast radius with limited rollback options.
**Do this instead:** Keep legacy default, ship opt-in flag, then promote with benchmark evidence.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Browser automation backend (DrissionPage now, Playwright possible) | Adapter boundary with `move_path` + action primitives | Engine remains driver-agnostic |
| Existing LLM/provider stack | No direct dependency | Cursor engine should not couple to solver/provider logic |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `agent/robotic.py` ↔ `agent/motion/facade.py` | Direct sync API call | Stable compatibility boundary |
| `agent/motion/facade.py` ↔ `tools/motion/human_engine.py` | Typed method contract | Supports A/B and fallback behavior |
| `tools/motion/human_engine.py` ↔ `browser/cursor_adapter.py` | Point-stream contract | Keeps transport specifics outside algorithm |

## Sources

- https://raw.githubusercontent.com/riflosnake/HumanCursor/main/README.md (official project docs, algorithm goals and API surface)
- https://raw.githubusercontent.com/patrikoss/pyclick/master/pyclick/humancurve.py (reference implementation pattern for bezier + distortion + tween pipeline)
- Internal architecture baseline:
  - `D:/hcaptcha-challenger/.planning/PROJECT.md`
  - `D:/hcaptcha-challenger/.planning/codebase/ARCHITECTURE.md`
  - `D:/hcaptcha-challenger/.planning/codebase/CONVENTIONS.md`

---
*Architecture research for: HumanCursor migration in hcaptcha-challenger*
*Researched: 2026-04-30*
