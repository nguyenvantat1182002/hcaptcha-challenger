"""Human-like mouse movement and clicking.

Trajectory generation inspired by HumanCursor:
- N-degree Bezier curves with random internal knots
- Gaussian distortion for micro-jitter
- Easing functions for natural velocity profiles
- Random curve parameters per movement

No external dependencies (pytweening/numpy inlined).
"""

from __future__ import annotations

import math
import random
import time
from typing import List, Protocol, Tuple

from hcaptcha_challenger.agent.mouse_config import HumanConfig, rand, rand_range, rand_int_range, sleep_ms


class RawMouse(Protocol):
    def move(self, x: float, y: float) -> None: ...
    def down(self) -> None: ...
    def up(self) -> None: ...
    def wheel(self, delta_x: float, delta_y: float) -> None: ...


class Point:
    __slots__ = ("x", "y")
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


# ---------------------------------------------------------------------------
# Easing functions (subset of pytweening, inlined)
# ---------------------------------------------------------------------------

def _ease_out_quad(t: float) -> float:
    return -t * (t - 2)


def _ease_out_cubic(t: float) -> float:
    t -= 1
    return t * t * t + 1


def _ease_out_expo(t: float) -> float:
    if t == 1.0:
        return 1.0
    return 1 - pow(2, -10 * t)


def _ease_in_out_sine(t: float) -> float:
    return -0.5 * (math.cos(math.pi * t) - 1)


def _ease_in_out_cubic(t: float) -> float:
    t *= 2
    if t < 1:
        return 0.5 * t * t * t
    t -= 2
    return 0.5 * (t * t * t + 2)


def _ease_in_out_quart(t: float) -> float:
    t *= 2
    if t < 1:
        return 0.5 * t * t * t * t
    t -= 2
    return -0.5 * (t * t * t * t - 2)


def _ease_in_out_quint(t: float) -> float:
    t *= 2
    if t < 1:
        return 0.5 * t * t * t * t * t
    t -= 2
    return 0.5 * (t * t * t * t * t + 2)


def _ease_linear(t: float) -> float:
    return t


_EASING_FUNCTIONS = [
    _ease_out_quad,
    _ease_out_cubic,
    _ease_out_expo,
    _ease_in_out_sine,
    _ease_in_out_cubic,
    _ease_in_out_quart,
    _ease_in_out_quint,
    _ease_linear,
]


# ---------------------------------------------------------------------------
# Bezier curve (N-degree, matching HumanCursor's BezierCalculator)
# ---------------------------------------------------------------------------

def _binomial(n: int, k: int) -> float:
    return math.factorial(n) / (math.factorial(k) * math.factorial(n - k))


def _bernstein_polynomial(points: List[Tuple[float, float]]):
    """Returns a function that evaluates the Bezier curve at parameter t."""
    n = len(points) - 1
    def bernstein(t: float) -> Tuple[float, float]:
        x = y = 0.0
        for i, (px, py) in enumerate(points):
            bern = _binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))
            x += px * bern
            y += py * bern
        return x, y
    return bernstein


def _calculate_bezier_points(n_points: int, control_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Generate n_points along a Bezier curve defined by control_points."""
    bernstein = _bernstein_polynomial(control_points)
    return [bernstein(i / max(n_points - 1, 1)) for i in range(n_points)]


# ---------------------------------------------------------------------------
# HumanCursor-style trajectory generation
# ---------------------------------------------------------------------------

def _generate_internal_knots(
    from_pt: Tuple[float, float],
    to_pt: Tuple[float, float],
    knots_count: int,
    offset_boundary_x: int,
    offset_boundary_y: int,
) -> List[Tuple[float, float]]:
    """Generate random internal knot points for the Bezier curve."""
    left = int(min(from_pt[0], to_pt[0])) - offset_boundary_x
    right = int(max(from_pt[0], to_pt[0])) + offset_boundary_x
    down = int(min(from_pt[1], to_pt[1])) - offset_boundary_y
    up = int(max(from_pt[1], to_pt[1])) + offset_boundary_y

    if left >= right:
        right = left + 1
    if down >= up:
        up = down + 1

    knots = []
    for _ in range(knots_count):
        kx = random.randint(left, right)
        ky = random.randint(down, up)
        knots.append((float(kx), float(ky)))
    return knots


def _distort_points(
    points: List[Tuple[float, float]],
    distortion_mean: float,
    distortion_st_dev: float,
    distortion_frequency: float,
) -> List[Tuple[float, float]]:
    """Apply Gaussian distortion to intermediate points."""
    if len(points) <= 2:
        return points
    distorted = [points[0]]
    for x, y in points[1:-1]:
        if random.random() < distortion_frequency:
            delta = random.gauss(distortion_mean, distortion_st_dev)
        else:
            delta = 0
        distorted.append((x, y + delta))
    distorted.append(points[-1])
    return distorted


def _tween_points(
    points: List[Tuple[float, float]],
    tween,
    target_points: int,
) -> List[Tuple[float, float]]:
    """Re-sample points using an easing function for velocity variation."""
    if target_points < 2:
        target_points = 2
    result = []
    for i in range(target_points):
        index = int(tween(float(i) / (target_points - 1)) * (len(points) - 1))
        index = min(index, len(points) - 1)
        result.append(points[index])
    return result


def _generate_random_curve_params(
    from_pt: Tuple[float, float],
    to_pt: Tuple[float, float],
) -> dict:
    """Generate randomized curve parameters (HumanCursor-style)."""
    tween = random.choice(_EASING_FUNCTIONS)

    offset_boundary_x = random.choice(
        random.choices(
            [range(20, 45), range(45, 75), range(75, 100)],
            weights=[0.2, 0.65, 0.15],
        )[0]
    )
    offset_boundary_y = random.choice(
        random.choices(
            [range(20, 45), range(45, 75), range(75, 100)],
            weights=[0.2, 0.65, 0.15],
        )[0]
    )
    knots_count = random.choices(
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        weights=[0.15, 0.36, 0.17, 0.12, 0.08, 0.04, 0.03, 0.02, 0.015, 0.005],
    )[0]

    distortion_mean = random.randint(80, 110) / 100
    distortion_st_dev = random.randint(85, 110) / 100
    distortion_frequency = random.randint(25, 70) / 100

    target_points = random.choice(
        random.choices(
            [range(35, 45), range(45, 60), range(60, 80)],
            weights=[0.53, 0.32, 0.15],
        )[0]
    )

    return {
        "tween": tween,
        "offset_boundary_x": offset_boundary_x,
        "offset_boundary_y": offset_boundary_y,
        "knots_count": knots_count,
        "distortion_mean": distortion_mean,
        "distortion_st_dev": distortion_st_dev,
        "distortion_frequency": distortion_frequency,
        "target_points": target_points,
    }


def generate_human_trajectory(
    from_pt: Tuple[float, float],
    to_pt: Tuple[float, float],
    steady: bool = False,
) -> List[Tuple[float, float]]:
    """Generate a complete human-like mouse trajectory between two points.

    Args:
        from_pt: Starting (x, y) coordinates.
        to_pt: Destination (x, y) coordinates.
        steady: If True, use minimal curve distortion (for precise operations).

    Returns:
        List of (x, y) points along the trajectory.
    """
    dist = math.hypot(to_pt[0] - from_pt[0], to_pt[1] - from_pt[1])
    if dist < 1:
        return [from_pt]

    params = _generate_random_curve_params(from_pt, to_pt)

    if steady:
        params["offset_boundary_x"] = 10
        params["offset_boundary_y"] = 10
        params["distortion_mean"] = 1.2
        params["distortion_st_dev"] = 1.2
        params["distortion_frequency"] = 1.0

    # Generate internal knots
    knots = _generate_internal_knots(
        from_pt, to_pt,
        params["knots_count"],
        params["offset_boundary_x"],
        params["offset_boundary_y"],
    )

    # Build control points: start + knots + end
    control_points = [from_pt] + knots + [to_pt]

    # Generate raw Bezier curve points
    mid_pts_count = max(int(dist), 2)
    raw_points = _calculate_bezier_points(mid_pts_count, control_points)

    # Apply Gaussian distortion
    distorted = _distort_points(
        raw_points,
        params["distortion_mean"],
        params["distortion_st_dev"],
        params["distortion_frequency"],
    )

    # Apply easing tween for velocity
    tweened = _tween_points(distorted, params["tween"], params["target_points"])

    return tweened


# ---------------------------------------------------------------------------
# High-level movement API
# ---------------------------------------------------------------------------

def human_move(
    raw: RawMouse,
    start_x: float, start_y: float,
    end_x: float, end_y: float,
    cfg: HumanConfig,
) -> None:
    """Move cursor from (start_x, start_y) to (end_x, end_y) with human-like trajectory.

    Speed is controlled by cfg.mouse_speed (0.5=fast, 1.0=normal, 2.0=slow)
    and cfg.mouse_move_delay_ms (per-point delay range in ms).
    """
    dist = math.hypot(end_x - start_x, end_y - start_y)
    if dist < 1:
        return

    trajectory = generate_human_trajectory(
        (start_x, start_y),
        (end_x, end_y),
    )

    speed = cfg.mouse_speed
    burst_counter = 0
    burst_size = rand_int_range(cfg.mouse_burst_size)

    for pt in trajectory:
        raw.move(round(pt[0]), round(pt[1]))

        # Per-point micro delay scaled by speed
        sleep_ms(rand_range(cfg.mouse_move_delay_ms) * speed)

        burst_counter += 1
        if burst_counter >= burst_size:
            sleep_ms(rand_range(cfg.mouse_burst_pause) * speed)
            burst_counter = 0


def click_target(box: dict, is_input: bool, cfg: HumanConfig) -> Point:
    """Pick a random click target within a bounding box."""
    if is_input:
        x_frac = rand_range(cfg.click_input_x_range)
        y_frac = rand(0.30, 0.70)
    else:
        x_frac = rand(0.35, 0.65)
        y_frac = rand(0.35, 0.65)
    return Point(round(box["x"] + box["width"] * x_frac),
                 round(box["y"] + box["height"] * y_frac))


def human_click(raw: RawMouse, is_input: bool, cfg: HumanConfig) -> None:
    """Perform a human-like click with aim delay and hold time."""
    aim_delay = rand_range(cfg.click_aim_delay_input) if is_input else rand_range(cfg.click_aim_delay_button)
    sleep_ms(aim_delay)
    hold_time = rand_range(cfg.click_hold_input) if is_input else rand_range(cfg.click_hold_button)
    raw.down()
    sleep_ms(hold_time)
    raw.up()


def human_idle(raw: RawMouse, seconds: float, cx: float, cy: float, cfg: HumanConfig) -> None:
    """Simulate idle micro-movements near a position."""
    end_time = time.monotonic() + seconds
    x, y = cx, cy
    while time.monotonic() < end_time:
        dx = (random.random() - 0.5) * 2 * cfg.idle_drift_px
        dy = (random.random() - 0.5) * 2 * cfg.idle_drift_px
        x += dx
        y += dy
        raw.move(round(x), round(y))
        sleep_ms(rand_range(cfg.idle_pause_range))
