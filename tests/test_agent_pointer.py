# -*- coding: utf-8 -*-
import pytest

from hcaptcha_challenger.agent.pointer import (
    generate_bezier_trajectory,
    generate_dynamic_delays,
    _generate_bezier_trajectory,
    _generate_dynamic_delays,
)


def test_bezier_trajectory_point_count_and_endpoints():
    start = (100.0, 150.0)
    end = (400.0, 500.0)
    steps = 25

    points = generate_bezier_trajectory(start, end, steps)

    assert len(points) == steps + 1
    # Check start point
    assert pytest.approx(points[0][0], rel=1e-5) == start[0]
    assert pytest.approx(points[0][1], rel=1e-5) == start[1]
    # Check end point
    assert pytest.approx(points[-1][0], rel=1e-5) == end[0]
    assert pytest.approx(points[-1][1], rel=1e-5) == end[1]


def test_bezier_trajectory_intermediate_smoothness():
    start = (0.0, 0.0)
    end = (200.0, 200.0)
    steps = 10

    points = generate_bezier_trajectory(start, end, steps)

    # Intermediate points should lie between bounds or within reasonable curve bounds
    for x, y in points:
        assert -100.0 <= x <= 300.0
        assert -100.0 <= y <= 300.0


def test_dynamic_delays_profile():
    steps = 20
    base_delay = 15

    delays = generate_dynamic_delays(steps, base_delay)

    assert len(delays) == steps + 1
    # All delays must be strictly positive
    assert all(d > 0 for d in delays)

    # Endpoints should generally be larger than midpoint due to ease-in-out profile
    start_delay = delays[0]
    mid_delay = delays[steps // 2]
    end_delay = delays[-1]

    # Accounting for random jitter (±10%), average ends should exceed average midpoint
    assert start_delay > mid_delay * 0.8
    assert end_delay > mid_delay * 0.8


def test_backward_compatibility_aliases():
    start = (10.0, 20.0)
    end = (50.0, 60.0)
    points = _generate_bezier_trajectory(start, end, 5)
    delays = _generate_dynamic_delays(5, 10)

    assert len(points) == 6
    assert len(delays) == 6
