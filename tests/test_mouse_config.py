import pytest
from hcaptcha_challenger.agent.mouse_config import HumanConfig, resolve_config

def test_human_config_new_fields():
    cfg = HumanConfig()
    # New fields should exist
    assert hasattr(cfg, "knots_count")
    assert hasattr(cfg, "distortion_mean")
    assert hasattr(cfg, "distortion_st_dev")
    assert hasattr(cfg, "distortion_frequency")
    assert hasattr(cfg, "offset_boundary_x")
    assert hasattr(cfg, "offset_boundary_y")
    assert hasattr(cfg, "target_points")
    assert hasattr(cfg, "mouse_move_delay_ms")

def test_human_config_legacy_fields_removed():
    cfg = HumanConfig()
    # Legacy fields should be gone
    assert not hasattr(cfg, "mouse_steps_divisor")
    assert not hasattr(cfg, "mouse_wobble_max")

def test_to_humancursor_dict():
    cfg = HumanConfig(
        knots_count=3,
        distortion_mean=1.5,
        distortion_st_dev=1.2,
        distortion_frequency=0.4,
        offset_boundary_x=120,
        offset_boundary_y=120,
        target_points=30
    )
    d = cfg.to_humancursor_dict()
    assert d["knots_count"] == 3
    assert d["distortion_mean"] == 1.5
    assert d["distortion_st_dev"] == 1.2
    assert d["distortion_frequency"] == 0.4
    assert d["offset_boundary_x"] == 120
    assert d["offset_boundary_y"] == 120
    assert d["target_points"] == 30

def test_presets_valid():
    default = resolve_config("default")
    careful = resolve_config("careful")
    
    assert default.knots_count > 0
    assert careful.knots_count > 0
    assert careful.target_points > default.target_points  # Careful should have more points

def test_validation():
    with pytest.raises(ValueError):
        HumanConfig(target_points=0)
    with pytest.raises(ValueError):
        HumanConfig(knots_count=-1)
