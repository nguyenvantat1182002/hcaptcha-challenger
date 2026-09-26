# -*- coding: utf-8 -*-
import json
import pytest
import httpx
from pathlib import Path

from hcaptcha_challenger.models import (
    ImageAreaSelectChallenge,
    ImageDragDropChallenge,
    PointCoordinate,
    SpatialPath,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient
from hcaptcha_challenger.tools.yescaptcha.adapters import (
    YesCaptchaPointReasoner,
    YesCaptchaPathReasoner,
)


@pytest.mark.asyncio
async def test_yescaptcha_point_reasoner(tmp_path):
    img_path = tmp_path / "area_view.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummy")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/createTask"
        payload = json.loads(request.content)
        assert payload["task"]["question"] == "click the center of all apples"
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {
                    "clicks": [
                        {"x": 168, "y": 266},
                        {"x": 263, "y": 273},
                    ]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaPointReasoner(client=client)

        response = await reasoner(
            challenge_screenshot=img_path,
            auxiliary_information="click the center of all apples",
        )

    assert isinstance(response, ImageAreaSelectChallenge)
    assert response.challenge_prompt == "click the center of all apples"
    assert len(response.points) == 2
    assert response.points[0] == PointCoordinate(x=168, y=266)
    assert response.points[1] == PointCoordinate(x=263, y=273)

    # Test cache_response
    cache_file = tmp_path / "point_answer.json"
    reasoner.cache_response(cache_file)
    assert cache_file.exists()


@pytest.mark.asyncio
async def test_yescaptcha_path_reasoner(tmp_path):
    img_path = tmp_path / "drag_view.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummy")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/createTask"
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {
                    "box": [
                        {"start": [418, 319], "end": [265, 319]},
                    ]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaPathReasoner(client=client)

        response = await reasoner(
            challenge_screenshot=img_path,
            auxiliary_information="drag the puzzle piece",
        )

    assert isinstance(response, ImageDragDropChallenge)
    assert len(response.paths) == 1
    assert response.paths[0].start_point == PointCoordinate(x=418, y=319)
    assert response.paths[0].end_point == PointCoordinate(x=265, y=319)

    # Test cache_response
    cache_file = tmp_path / "path_answer.json"
    reasoner.cache_response(cache_file)
    assert cache_file.exists()


def test_area_select_and_drag_drop_solvers_use_yescaptcha_reasoner():
    from unittest.mock import MagicMock
    from hcaptcha_challenger.agent.config import AgentConfig
    from hcaptcha_challenger.agent.solvers.select import AreaSelectSolver
    from hcaptcha_challenger.agent.solvers.drag import DragDropSolver

    config = AgentConfig(
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="test_key_xyz",
    )
    mock_driver = MagicMock()
    mock_pointer = MagicMock()

    area_solver = AreaSelectSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    assert isinstance(area_solver._spatial_point_reasoner, YesCaptchaPointReasoner)

    drag_solver = DragDropSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    assert isinstance(drag_solver._spatial_path_reasoner, YesCaptchaPathReasoner)


@pytest.mark.asyncio
async def test_yescaptcha_point_reasoner_with_bbox(tmp_path):
    from PIL import Image

    img_path = tmp_path / "area_real.png"
    Image.new("RGB", (500, 400), color="blue").save(img_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {
                    "clicks": [
                        {"x": 50, "y": 60},
                    ]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaPointReasoner(client=client)

        # bbox: x=100, y=200, width=1000 (scale 2.0), height=800 (scale 2.0)
        bbox = {"x": 100, "y": 200, "width": 1000, "height": 800}
        response = await reasoner(
            challenge_screenshot=img_path,
            auxiliary_information="find the item",
            bbox=bbox,
        )

    assert len(response.points) == 1
    # 100 + 50 * 2 = 200, 200 + 60 * 2 = 320
    assert response.points[0] == PointCoordinate(x=200, y=320)


@pytest.mark.asyncio
async def test_yescaptcha_path_reasoner_with_bbox(tmp_path):
    from PIL import Image

    img_path = tmp_path / "drag_real.png"
    Image.new("RGB", (500, 400), color="green").save(img_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {
                    "box": [
                        {"start": [50, 60], "end": [100, 120]},
                    ]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaPathReasoner(client=client)

        bbox = {"x": 100, "y": 200, "width": 1000, "height": 800}
        response = await reasoner(
            challenge_screenshot=img_path,
            auxiliary_information="drag the item",
            bbox=bbox,
        )

    assert len(response.paths) == 1
    assert response.paths[0].start_point == PointCoordinate(x=200, y=320)
    assert response.paths[0].end_point == PointCoordinate(x=300, y=440)


