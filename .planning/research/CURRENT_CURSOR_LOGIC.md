# Current Cursor Movement Implementation

**Project:** hcaptcha-challenger
**Researched:** 2025-04-12
**Overall confidence:** HIGH

## Overview

The current cursor movement in `hcaptcha-challenger` is a custom implementation designed to mimic human behavior using Bezier curves and randomized distortions. It is tightly integrated into the `RoboticArm` execution engine.

## Logic Location

### 1. Trajectory Generation: `src/hcaptcha_challenger/agent/mouse.py`
This file contains the core algorithms for generating human-like paths.
- **Bezier Curves:** Uses N-degree Bezier curves with randomized internal knots to create non-linear paths.
- **Distortion:** Applies Gaussian distortion to intermediate points for micro-jitter.
- **Velocity Profiles:** Inlines easing functions (similar to `pytweening`) to vary movement speed across the trajectory.
- **Randomization:** Parameters like knot counts, offset boundaries, and distortion frequency are randomized per movement.

### 2. Configuration & Presets: `src/hcaptcha_challenger/agent/mouse_config.py`
Centralizes all numeric parameters for human-like behavior.
- **Presets:** Defines `default` (normal) and `careful` (slower, more precise) configurations.
- **Tunables:** Includes mouse speed, movement delay, burst sizes, click hold times, and idle drift.

### 3. Execution Adapter: `src/hcaptcha_challenger/agent/robotic.py`
Integrates the trajectory logic with the browser driver.
- **`DrissionPageMouse`:** An adapter that implements the `RawMouse` protocol required by `mouse.py`.
- **CDP Interaction:** Uses `Input.dispatchMouseEvent` via DrissionPage to send raw mouse events directly to the browser, bypassing high-level driver abstractions that might impose their own (often linear) movement logic.
- **Coordinate Mapping:** Handles translation between iframe-local coordinates and absolute page viewport coordinates.

## Calling Patterns

The `RoboticArm` class orchestrates all cursor movements through the following methods:

| Method | Cursor Logic Flow |
|--------|-------------------|
| `click_element(element)` | `click_target` (get point) → `human_move` (bezier path) → `human_click` (hold/release) |
| `click_at(x, y)` | `human_move` (bezier path) → `human_click` (hold/release) |
| `_perform_drag_drop(path)` | `human_move` (to start) → `raw.down()` → `human_move` (bezier path to end) → `raw.up()` |

## Dependencies

### Internal Dependencies
- `hcaptcha_challenger.agent.mouse_config`: Supplies `HumanConfig` and utility functions (`rand`, `sleep_ms`).
- `hcaptcha_challenger.agent.mouse`: Supplies movement and click algorithms.

### External Dependencies
- **Standard Library:** `math`, `random`, `time`.
- **DrissionPage:** Used in `robotic.py` to obtain element positions and dispatch low-level CDP events.

## Key Protocols

The system uses a `RawMouse` protocol (defined in `mouse.py`) to decouple trajectory generation from execution:

```python
class RawMouse(Protocol):
    def move(self, x: float, y: float) -> None: ...
    def down(self) -> None: ...
    def up(self) -> None: ...
    def wheel(self, delta_x: float, delta_y: float) -> None: ...
```

## Observations for Migration

- The current logic in `mouse.py` is largely a manual implementation of what the `HumanCursor` library provides.
- The `DrissionPageMouse` adapter is the critical bridge that must be maintained or updated to support `HumanCursor`.
- The `HumanConfig` in `mouse_config.py` contains many parameters that may need to be mapped to `HumanCursor` configuration objects.
