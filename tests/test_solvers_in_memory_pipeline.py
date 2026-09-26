from unittest.mock import AsyncMock, MagicMock

import pytest

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.solvers.base import ChallengeContext
from hcaptcha_challenger.agent.solvers.drag import DragDropSolver
from hcaptcha_challenger.agent.solvers.select import AreaSelectSolver
from hcaptcha_challenger.models import (
    ChallengeImage,
    ChallengeTypeEnum,
    ImageAreaSelectChallenge,
    ImageDragDropChallenge,
    PointCoordinate,
    SpatialPath,
)


@pytest.mark.asyncio
async def test_area_select_solver_bypasses_grid_projection_with_yescaptcha(tmp_path):
    config = AgentConfig(
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="fake_key",
        enable_challenger_debug=False,
    )
    mock_driver = MagicMock()
    mock_driver.page = AsyncMock()
    mock_pointer = AsyncMock()

    # In-memory image
    challenge_image = ChallengeImage.from_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_bbox = {"x": 100, "y": 200, "width": 400, "height": 300}
    mock_driver.capture_challenge_image = AsyncMock(return_value=(challenge_image, fake_bbox))
    mock_driver.create_spatial_projection = MagicMock()

    solver = AreaSelectSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    # Reasoner has requires_grid_projection = False
    assert getattr(solver._spatial_point_reasoner, "requires_grid_projection", True) is False

    mock_reasoner = AsyncMock(return_value=ImageAreaSelectChallenge(
        challenge_prompt="click apple",
        points=[PointCoordinate(x=150, y=250)]
    ))
    mock_reasoner.requires_grid_projection = False
    solver._spatial_point_reasoner = mock_reasoner

    ctx = ChallengeContext(
        frame=MagicMock(),
        job_type=ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
        cache_key=tmp_path / "cache_round",
        crumb_count=1,
        payload=None,
    )

    await solver.solve(ctx)

    # 1. Grid projection was completely bypassed (0 Matplotlib calls)
    mock_driver.create_spatial_projection.assert_not_called()

    # 2. Reasoner received in-memory ChallengeImage directly with grid_divisions=None
    mock_reasoner.assert_awaited_once_with(
        challenge_screenshot=challenge_image,
        grid_divisions=None,
        auxiliary_information="Please note that the current task type is: image_label_single_select",
        payload=None,
        bbox=fake_bbox,
    )

    # 3. Pointer clicked the resolved point
    mock_pointer.click_at.assert_awaited_once_with(150, 250, delay=180)

    # 4. Zero debug files written to cache_key directory
    assert list(tmp_path.glob("**/*")) == []


@pytest.mark.asyncio
async def test_drag_drop_solver_bypasses_grid_projection_with_yescaptcha(tmp_path):
    config = AgentConfig(
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="fake_key",
        enable_challenger_debug=False,
    )
    mock_driver = MagicMock()
    mock_driver.page = AsyncMock()
    mock_pointer = AsyncMock()

    challenge_image = ChallengeImage.from_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_bbox = {"x": 50, "y": 60, "width": 500, "height": 400}
    mock_driver.capture_challenge_image = AsyncMock(return_value=(challenge_image, fake_bbox))
    mock_driver.create_spatial_projection = MagicMock()

    solver = DragDropSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    assert getattr(solver._spatial_path_reasoner, "requires_grid_projection", True) is False

    path = SpatialPath(
        start_point=PointCoordinate(x=100, y=100),
        end_point=PointCoordinate(x=200, y=200),
    )
    mock_reasoner = AsyncMock(return_value=ImageDragDropChallenge(
        challenge_prompt="drag piece",
        paths=[path]
    ))
    mock_reasoner.requires_grid_projection = False
    solver._spatial_path_reasoner = mock_reasoner

    ctx = ChallengeContext(
        frame=MagicMock(),
        job_type=ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
        cache_key=tmp_path / "cache_round_drag",
        crumb_count=1,
        payload=None,
    )

    await solver.solve(ctx)

    # Grid projection bypassed
    mock_driver.create_spatial_projection.assert_not_called()

    # Reasoner received ChallengeImage and grid_divisions=None
    mock_reasoner.assert_awaited_once_with(
        challenge_screenshot=challenge_image,
        grid_divisions=None,
        auxiliary_information="Please note that the current task type is: image_drag_single",
        payload=None,
        bbox=fake_bbox,
    )

    # Pointer dragged path
    mock_pointer.drag.assert_awaited_once_with(path)

    # Zero files written to cache_key directory
    assert list(tmp_path.glob("**/*")) == []


@pytest.mark.asyncio
async def test_area_select_solver_writes_debug_file_when_enabled(tmp_path):
    config = AgentConfig(
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="fake_key",
        enable_challenger_debug=True,
    )
    mock_driver = MagicMock()
    mock_driver.page = AsyncMock()
    mock_pointer = AsyncMock()

    challenge_image = ChallengeImage.from_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_bbox = {"x": 100, "y": 200, "width": 400, "height": 300}
    mock_driver.capture_challenge_image = AsyncMock(return_value=(challenge_image, fake_bbox))

    mock_reasoner = AsyncMock(return_value=ImageAreaSelectChallenge(
        challenge_prompt="click apple",
        points=[PointCoordinate(x=150, y=250)]
    ))
    mock_reasoner.requires_grid_projection = False
    mock_reasoner.cache_response = MagicMock()

    solver = AreaSelectSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    solver._spatial_point_reasoner = mock_reasoner

    cache_dir = tmp_path / "cache_round_debug"
    ctx = ChallengeContext(
        frame=MagicMock(),
        job_type=ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
        cache_key=cache_dir,
        crumb_count=1,
        payload=None,
    )

    await solver.solve(ctx)

    # When debug is enabled, debug file was written to disk
    debug_file = cache_dir / f"{cache_dir.name}_0_challenge_view.png"
    assert debug_file.exists()
    assert debug_file.read_bytes() == b"\x89PNG\r\n\x1a\nfake"


@pytest.mark.asyncio
async def test_area_select_solver_calls_grid_projection_when_required(tmp_path):
    config = AgentConfig(
        REASONING_PROVIDER="gemini",
        GEMINI_API_KEY="fake_key",
        enable_challenger_debug=False,
    )
    mock_driver = MagicMock()
    mock_driver.page = AsyncMock()
    mock_pointer = AsyncMock()

    challenge_image = ChallengeImage.from_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_bbox = {"x": 100, "y": 200, "width": 400, "height": 300}
    mock_driver.capture_challenge_image = AsyncMock(return_value=(challenge_image, fake_bbox))
    mock_driver.create_spatial_projection = MagicMock(return_value=10)

    mock_reasoner = AsyncMock(return_value=ImageAreaSelectChallenge(
        challenge_prompt="click apple",
        points=[PointCoordinate(x=150, y=250)]
    ))
    mock_reasoner.requires_grid_projection = True

    solver = AreaSelectSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    solver._spatial_point_reasoner = mock_reasoner

    cache_dir = tmp_path / "cache_round_gemini"
    ctx = ChallengeContext(
        frame=MagicMock(),
        job_type=ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
        cache_key=cache_dir,
        crumb_count=1,
        payload=None,
    )

    await solver.solve(ctx)

    mock_driver.create_spatial_projection.assert_called_once_with(
        challenge_image=challenge_image,
        bbox=fake_bbox,
        cache_key=cache_dir,
        crumb_id=0,
    )
    mock_reasoner.assert_awaited_once_with(
        challenge_screenshot=challenge_image,
        grid_divisions=10,
        auxiliary_information="Please note that the current task type is: image_label_single_select",
        payload=None,
        bbox=fake_bbox,
    )

