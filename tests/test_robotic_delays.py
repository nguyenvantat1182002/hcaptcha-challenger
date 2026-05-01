import pytest
json = __import__('json')
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
from hcaptcha_challenger.agent.robotic import RoboticArm
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.mouse_config import HumanConfig

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.MOUSE_SPEED = 1.0
    config.custom_skills_path = None
    config.enable_challenger_debug = False
    config.OPENROUTER_API_KEY.get_secret_value.return_value = "fake_key"
    config.CHALLENGE_CLASSIFIER_MODEL = "fake_model"
    config.IMAGE_CLASSIFIER_MODEL = "fake_model"
    config.SPATIAL_PATH_REASONER_MODEL = "fake_model"
    config.SPATIAL_POINT_REASONER_MODEL = "fake_model"
    config.telemetry_dir = Path("tmp/.telemetry")
    config.cache_dir = Path("tmp/.cache")
    config.challenge_dir = Path("tmp/.challenge")
    config.coordinate_grid = MagicMock()
    config.create_cache_key.return_value = Path("tmp/.cache/test")
    return config

@pytest.fixture
def mock_page():
    page = MagicMock()
    # Mock tab and actions for DrissionPageMouse
    page.tab.actions = MagicMock()
    return page

def test_robotic_arm_init_selects_persona(mock_page, mock_config):
    with patch('hcaptcha_challenger.agent.robotic.select_random_persona') as mock_select:
        mock_select.return_value = ("test_persona", HumanConfig())
        arm = RoboticArm(mock_page, mock_config)
        assert arm._persona_name == "test_persona"
        mock_select.assert_called_once()

def test_record_outcome(mock_page, mock_config, tmp_path):
    mock_config.telemetry_dir = tmp_path / ".telemetry"
    arm = RoboticArm(mock_page, mock_config)
    arm._persona_name = "test_persona"
    
    arm._record_outcome(True)
    
    telemetry_file = mock_config.telemetry_dir / "telemetry.json"
    assert telemetry_file.exists()
    
    with open(telemetry_file, "r") as f:
        line = f.readline()
        record = json.loads(line)
        assert record["persona"] == "test_persona"
        assert record["success"] is True
        assert "timestamp" in record

@patch('hcaptcha_challenger.agent.robotic.sleep_ms')
def test_recognition_delay_applied(mock_sleep, mock_page, mock_config):
    arm = RoboticArm(mock_page, mock_config)
    arm._human_cfg.recognition_delay = (100, 200)
    
    # Mock classifier response
    mock_response = MagicMock()
    mock_response.convert_box_to_boolean_matrix.return_value = [True]
    arm._image_classifier = MagicMock(return_value=mock_response)
    
    # Mock other methods needed for challenge_image_label_binary
    arm.check_crumb_count = MagicMock(return_value=1)
    arm._wait_for_all_loaders_complete = MagicMock()
    arm.screenshot_element_in_frame = MagicMock()
    arm.get_challenge_frame_locator = MagicMock()
    arm.click_element = MagicMock()
    
    # Mock DOM elements
    mock_frame = arm.get_challenge_frame_locator()
    mock_frame.ele.return_value = MagicMock()
    
    arm.challenge_image_label_binary()
    
    # Verify sleep_ms was called with value in range (100, 200)
    mock_sleep.assert_called()
    # Find the call with recognition delay. 
    # Note: there might be other calls to sleep_ms (e.g. in click_element but we mocked it)
    # Actually, the only sleep_ms in challenge_image_label_binary is the recognition delay.
    
    found_delay = False
    for call in mock_sleep.call_args_list:
        delay = call[0][0]
        if 100 <= delay <= 200:
            found_delay = True
            break
    assert found_delay, f"No sleep call found within range (100, 200). Calls: {mock_sleep.call_args_list}"
