import pytest
from unittest.mock import MagicMock
from hcaptcha_challenger.agent.mouse import human_move, RawMouse
from hcaptcha_challenger.agent.mouse_config import HumanConfig

class MockRawMouse:
    def __init__(self):
        self.move_calls = []
        self.down_calls = 0
        self.up_calls = 0

    def move(self, x: float, y: float):
        self.move_calls.append((x, y))

    def down(self):
        self.down_calls += 1

    def up(self):
        self.up_calls += 1
    
    def wheel(self, dx, dy):
        pass

def test_human_move_integrates_humancursor():
    raw = MockRawMouse()
    cfg = HumanConfig(target_points=10)
    
    human_move(raw, 0, 0, 100, 100, cfg)
    
    # Should have called move multiple times
    assert len(raw.move_calls) >= 2
    
    # Coordinates should be rounded (integers)
    for x, y in raw.move_calls:
        assert isinstance(x, int)
        assert isinstance(y, int)
    
    # Should end near or at (100, 100)
    # humancursor's HumanizeMouseTrajectory might not end exactly at target if not configured?
    # Actually, it should end at target.
    last_x, last_y = raw.move_calls[-1]
    assert last_x == 100
    assert last_y == 100

def test_legacy_math_removed():
    import hcaptcha_challenger.agent.mouse as mouse
    assert not hasattr(mouse, "_binomial")
    assert not hasattr(mouse, "_bernstein_polynomial")
    assert not hasattr(mouse, "_ease_out_quad")
