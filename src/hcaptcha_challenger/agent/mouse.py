"""Human-like mouse movement and clicking.

Trajectory generation powered by humancursor library.
"""

from __future__ import annotations

import math
import random
import time
from typing import List, Protocol, Tuple

from humancursor.utilities.human_curve_generator import HumanizeMouseTrajectory
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
        raw.move(round(end_x), round(end_y))
        return

    # Use humancursor to generate trajectory
    curve = HumanizeMouseTrajectory(
        from_point=(start_x, start_y),
        to_point=(end_x, end_y),
        **cfg.to_humancursor_dict()
    )
    
    trajectory = curve.points

    speed = cfg.mouse_speed
    burst_counter = 0
    burst_size = rand_int_range(cfg.mouse_burst_size)

    for x, y in trajectory:
        # MANDATORY rounding per Pitfall 1
        raw.move(round(x), round(y))

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
