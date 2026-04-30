# Architecture Research

**Domain:** Python browser automation cursor movement migration (HumanCursor-style)
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                    Public Orchestration API (Stable)                      │
├────────────────────────────────────────────────────────────────────────────┤
│  AgentV / RoboticArm                                                      │
│  - click_element()  - click_at()  - _perform_drag_drop()                 │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ intent (move/click/drag)
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                   Cursor Facade + Policy Layer (New)                      │
├────────────────────────────────────────────────────────────────────────────┤
│  CursorController                                                         │
│  - move_to_point()  - click()  - drag_path()                             │
│  - chooses strategy from config                                           │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ sampled points + timing
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              Motion Engine Layer (HumanCursor-style strategy)             │
├────────────────────────────────────────────────────────────────────────────┤
│  TrajectoryGenerator + TimingProfile + TargetSelector                     │
│  - bezier/spline path generation                                          │
│  - easing + jitter + burst pauses                                         │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ primitive commands
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    Backend Mouse Adapter Layer                             │
├────────────────────────────────────────────────────────────────────────────┤
│  WebMouseAdapter (DrissionPage/Playwright/Selenium)                       │
│  SystemMouseAdapter (optional, later)                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `RoboticArm` (existing) | Produces interaction intent from challenge-solving flow | Keep current methods and delegate internals to cursor facade |
| `CursorController` (new) | Single boundary for all cursor actions; keeps API compatibility | New class in `agent/` with methods matching existing intent granularity |
| `TrajectoryGenerator` | Creates natural path points (start/end/control points/distortion) | Strategy object wrapping current `generate_human_trajectory()` behavior |
| `TimingProfile` | Applies human-like velocity, pauses, click hold timing | Encapsulate `mouse_speed`, burst, hold, aim delay parameters |
| `TargetSelector` | Selects non-center click positions inside element bbox | Reuse and isolate `click_target()` logic |
| `WebMouseAdapter` | Converts normalized/local points to browser backend calls | Adapter over `DrissionPageMouse` now, extendable to Playwright/Selenium |
| `MotionMetricsProbe` (new) | Captures movement metrics for parity/regression tests | Lightweight recorder used only in tests/benchmark mode |

## Recommended Project Structure

```text
src/
└── hcaptcha_challenger/
    ├── agent/
    │   ├── robotic.py                 # Keep public orchestration behavior stable
    │   ├── cursor_controller.py       # New facade boundary for cursor intents
    │   ├── mouse.py                   # Human trajectory and click primitives
    │   ├── mouse_config.py            # Movement/timing config and presets
    │   └── adapters/
    │       ├── mouse_protocol.py      # Backend protocol (move/down/up/wheel)
    │       └── drission_mouse.py      # Drission-specific implementation
    └── tests/
        ├── test_cursor_controller.py  # Contract tests for compatibility
        ├── test_mouse_trajectory.py   # Deterministic/statistical movement tests
        └── test_motion_parity.py      # Benchmark against parity thresholds
```

### Structure Rationale

- **`agent/cursor_controller.py`:** isolates migration risk to one seam and prevents widespread API churn in `RoboticArm`.
- **`agent/adapters/`:** separates "how to move a backend mouse" from "how to generate human motion", enabling backend swaps without touching movement math.
- **`mouse.py` + `mouse_config.py`:** retain as engine/config center; avoid rewriting already-integrated movement core.
- **`tests/test_motion_parity.py`:** makes quantitative parity a first-class artifact, not ad-hoc manual checking.

## Architectural Patterns

### Pattern 1: Facade at Integration Boundary

**What:** Keep existing high-level methods (`click_element`, `click_at`, drag flow), but route all cursor side effects through a new facade.
**When to use:** Brownfield migrations where orchestration API must stay stable.
**Trade-offs:** Adds one indirection layer, but sharply reduces breakage risk.

**Example:**
```python
class CursorController:
    def __init__(self, adapter, engine, policy):
        self.adapter = adapter
        self.engine = engine
        self.policy = policy

    def click_bbox(self, bbox, is_input=False):
        target = self.engine.pick_target(bbox, is_input=is_input)
        self.move_to_point(target.x, target.y)
        self.engine.perform_click(self.adapter, is_input=is_input)
```

### Pattern 2: Strategy for Motion Profiles

**What:** Treat trajectory generation as pluggable strategies (`legacy`, `humancursor_style`, `steady`).
**When to use:** Need A/B parity testing and safe fallback.
**Trade-offs:** Slightly more config complexity; major gain in controlled rollout.

**Example:**
```python
strategy = strategy_registry.resolve(config.cursor_strategy)  # "legacy" or "humancursor_style"
points = strategy.generate_path(start, end, steady=config.cursor_steady_mode)
```

### Pattern 3: Adapter for Automation Backends

**What:** Define minimal mouse primitive protocol and implement per backend.
**When to use:** Same movement engine must work with DrissionPage today and other browser drivers later.
**Trade-offs:** Requires explicit coordinate conversion rules per backend.

## Data Flow

### Request Flow (explicit direction)

```text
Challenge intent in RoboticArm
    ↓
CursorController (translate intent -> motion plan)
    ↓
Motion Engine (trajectory + timing)
    ↓
WebMouseAdapter (iframe-local -> viewport coords)
    ↓
Browser backend mouse events (move/down/up/wheel)
    ↓
hCaptcha UI state change
```

### State Management

```text
AgentConfig + MouseConfig
    ↓ (read-only at runtime)
CursorController session state (current x/y, strategy id)
    ↓
MotionMetricsProbe (optional, test mode only)
```

### Key Data Flows

1. **Element click flow:** `element bbox -> target selector -> trajectory points -> adapter.move* -> down/up`.
2. **Drag flow:** `reasoner path (normalized) -> projection to real bbox -> move/down/move/up`.
3. **Parity benchmark flow:** `captured movement trace -> metrics extractor -> threshold assertion`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| DrissionPage actions/CDP | Backend adapter calls primitive mouse operations | Current production path; preserve as default backend |
| Playwright mouse API | Optional future backend adapter | Official API supports `move/down/up/wheel`; interpolation available via `steps` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `RoboticArm` ↔ `CursorController` | Direct method calls | Compatibility seam; no CLI/public API change required |
| `CursorController` ↔ motion engine | Strategy interface | Enables fallback and staged rollout |
| motion engine ↔ backend adapter | Primitive protocol (`move/down/up/wheel`) | Keeps math decoupled from browser APIs |
| parity tests ↔ movement layer | Trace hooks/metrics output | Needed to enforce quantitative migration gate |

## Build Order Implications

1. **Introduce interfaces and facade without behavior change.**
   - Add `CursorController` and adapter protocol.
   - Wire `RoboticArm` to facade while still calling current movement logic.
2. **Extract current Human-like logic into explicit engine strategy.**
   - Move path/timing/target logic into strategy classes.
   - Keep defaults matching current behavior.
3. **Add HumanCursor-style strategy and config switch.**
   - Implement/align trajectory and timing profile.
   - Feature-flag with safe fallback to legacy strategy.
4. **Add quantitative parity tests and thresholds.**
   - Validate path curvature, velocity profile, and click dispersion distributions.
5. **Promote strategy to default after regressions pass.**
   - Keep legacy strategy for rollback window until stable.

This order minimizes API breakage because migration happens behind the `RoboticArm` boundary first, then behavior changes are rolled out under strategy control.

## Anti-Patterns

### Anti-Pattern 1: Mixing trajectory math directly into challenge handlers

**What people do:** Put movement randomization and backend event calls inline inside each challenge method.
**Why it's wrong:** Duplicates logic and makes parity validation impossible across flows.
**Do this instead:** Route all cursor actions through `CursorController` and engine strategy interfaces.

### Anti-Pattern 2: Backend-coupled movement generation

**What people do:** Encode DrissionPage or Selenium coordinate assumptions in the trajectory generator.
**Why it's wrong:** Prevents backend portability and causes hidden coordinate bugs.
**Do this instead:** Keep generator backend-agnostic; handle coordinate translation only inside adapters.

## Sources

- [Playwright Python Mouse API](https://playwright.dev/python/docs/api/class-mouse) (official docs, high-confidence for backend primitives)
- [HumanCursor on PyPI](https://pypi.org/project/HumanCursor/) (official package metadata + README; medium-confidence for architecture conventions)
- [riflosnake/HumanCursor repository](https://github.com/riflosnake/HumanCursor) (project reference; limited fetched detail in this run)
- Internal code context:
  - `src/hcaptcha_challenger/agent/robotic.py`
  - `src/hcaptcha_challenger/agent/mouse.py`
  - `src/hcaptcha_challenger/agent/mouse_config.py`
  - `.planning/codebase/ARCHITECTURE.md`

---
*Architecture research for: cursor movement migration in hcaptcha-challenger*
*Researched: 2026-04-30*
# Architecture Research

**Domain:** Cursor movement engine migration in existing Python captcha automation
**Researched:** 2026-04-30
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Interaction Orchestration               │
├─────────────────────────────────────────────────────────────┤
│  AgentV / RoboticArm selects movement intent               │
│  (move-to, click-approach, drag segment)                   │
├─────────────────────────────────────────────────────────────┤
│                    Movement Strategy Layer                 │
├─────────────────────────────────────────────────────────────┤
│  Compatibility Adapter  ->  HumanCursorStyleEngine         │
│  Profile Resolver       ->  Trajectory Generator           │
├─────────────────────────────────────────────────────────────┤
│                    Browser Execution Layer                 │
├─────────────────────────────────────────────────────────────┤
│  Playwright/DrissionPage events + timing + retries         │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Compatibility Adapter | Preserve old API and map to new engine calls | Facade preserving old method signatures. |
| HumanCursorStyleEngine | Generate path points and velocity/timing | Profile-driven algorithm module with seeded randomness. |
| Benchmark Harness | Validate parity and regressions | Test utilities comparing trajectory metrics vs reference envelopes. |

## Recommended Project Structure

```text
src/hcaptcha_challenger/agent/
├── movement/                     # Movement engine and contracts
│   ├── profiles.py               # Profile schemas/default presets
│   ├── trajectory.py             # Path + velocity generator
│   ├── adapter.py                # Backward-compatible API bridge
│   └── metrics.py                # Parity metrics and score utilities
├── robotic.py                    # Orchestrator integration points
└── config.py                     # Runtime flags / deterministic mode
tests/
├── movement/
│   ├── test_trajectory.py
│   ├── test_adapter_compat.py
│   └── test_parity_metrics.py
```

### Structure Rationale

- **`movement/` submodule:** isolates migration blast radius and keeps `robotic.py` lean.
- **`adapter.py`:** enforces compatibility-first rollout while allowing gradual extension.

## Architectural Patterns

### Pattern 1: Strategy + Profile Injection

**What:** Movement behavior selected by profile, not hardcoded branches.
**When to use:** Multiple challenge styles or progressive rollout.
**Trade-offs:** Slightly more abstraction but better testability and safer evolution.

### Pattern 2: Adapter for Backward Compatibility

**What:** Keep existing call signature and delegate to new engine.
**When to use:** Brownfield systems with external consumers.
**Trade-offs:** Temporary indirection; worth it to avoid API breakage.

### Pattern 3: Deterministic Test Mode

**What:** Seeded randomness path for repeatable benchmark runs.
**When to use:** CI, baseline generation, regression triage.
**Trade-offs:** Slight behavior difference from stochastic runtime, acceptable for testing.

## Data Flow

### Request Flow

```text
[Challenge intent]
    ↓
[RoboticArm] → [Compatibility Adapter] → [HumanCursorStyleEngine]
    ↓                                            ↓
[Browser actions] ← [point/timing sequence] ← [profile + seed]
```

### Key Data Flows

1. **Move intent flow:** target coords + profile -> generated trajectory -> browser step events.
2. **Validation flow:** generated trajectory -> metrics extractor -> parity score report.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Local/CI only | In-process generation is enough; focus on deterministic tests. |
| High challenge throughput | Cache profile transforms and reduce per-step allocations. |
| Multi-worker pipelines | Standardize config and seed strategy across workers. |

## Anti-Patterns

### Anti-Pattern 1: Monolithic Motion Logic Inside `robotic.py`

**What people do:** Keep all curve/timing math inline in orchestration file.
**Why it's wrong:** Hard to test, high merge risk, brittle changes.
**Do this instead:** Extract engine module and keep orchestrator focused on intent/execution.

### Anti-Pattern 2: "Visual Similarity Only" Validation

**What people do:** Judge migration by eyeballing movement clips.
**Why it's wrong:** Subjective and regression-prone.
**Do this instead:** Use measurable parity metrics with thresholds in CI.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `agent/robotic.py` ↔ `agent/movement/adapter.py` | direct API | Stable contract and compatibility defaults. |
| `movement/trajectory.py` ↔ tests | fixtures + metrics API | Enables benchmark-based quality gates. |

## Sources

- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- HumanCursor reference: [riflosnake/HumanCursor](https://github.com/riflosnake/HumanCursor)

---
*Architecture research for: cursor movement migration*
*Researched: 2026-04-30*
