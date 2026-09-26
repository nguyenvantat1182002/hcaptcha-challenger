import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.driver import BrowserArm
from hcaptcha_challenger.models import ChallengeImage


def _create_test_image_bytes(width: int = 300, height: int = 200) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color="blue")
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_browser_arm_capture_challenge_image_in_memory():
    # 1. Setup mock page and locator
    mock_page = MagicMock()
    config = AgentConfig()
    arm = BrowserArm(page=mock_page, config=config)

    fake_bytes = _create_test_image_bytes(300, 200)
    fake_bbox = {"x": 50.0, "y": 60.0, "width": 300.0, "height": 200.0}

    mock_locator = AsyncMock()
    mock_locator.screenshot.return_value = fake_bytes
    mock_locator.bounding_box.return_value = fake_bbox

    mock_frame = MagicMock()
    mock_frame.locator.return_value = mock_locator

    # 2. Invoke in-memory capture
    challenge_image, bbox = await arm.capture_challenge_image(mock_frame)

    # 3. Assertions
    assert isinstance(challenge_image, ChallengeImage)
    assert challenge_image.dimensions == (300, 200)
    assert challenge_image.raw_bytes == fake_bytes
    assert bbox == fake_bbox
    mock_locator.screenshot.assert_awaited_once_with(type="png")


@pytest.mark.asyncio
async def test_browser_arm_capture_spatial_mapping_backward_compatibility(tmp_path):
    mock_page = MagicMock()
    config = AgentConfig()
    arm = BrowserArm(page=mock_page, config=config)

    fake_bytes = _create_test_image_bytes(100, 100)
    fake_bbox = {"x": 10.0, "y": 20.0, "width": 100.0, "height": 100.0}

    mock_locator = AsyncMock()
    mock_locator.screenshot.return_value = fake_bytes
    mock_locator.bounding_box.return_value = fake_bbox

    mock_frame = MagicMock()
    mock_frame.locator.return_value = mock_locator

    cache_dir = tmp_path / "cache_round"
    cache_dir.mkdir()

    raw_path, proj_path = await arm.capture_spatial_mapping(mock_frame, cache_dir, 0)

    assert raw_path.exists()
    assert proj_path.exists()
    assert raw_path.read_bytes() == fake_bytes
