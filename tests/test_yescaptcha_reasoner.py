import base64
import json

import httpx
import pytest

from hcaptcha_challenger.models import CaptchaPayload, CaptchaTask, ImageBinaryChallenge
from hcaptcha_challenger.tools.yescaptcha.adapters import YesCaptchaBinaryReasoner
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient


@pytest.mark.asyncio
async def test_binary_reasoner_with_payload_urls(tmp_path):
    # Mock YesCaptcha API returning objects: [True, False, False, False, True, False, False, False, False]
    # Indices 0 -> [0, 0], 4 -> [1, 1]
    dummy_img_bytes = b"fake_png_data"
    expected_b64 = base64.b64encode(dummy_img_bytes).decode("utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and "example.com" in request.url.host:
            return httpx.Response(200, content=dummy_img_bytes)

        if request.url.path == "/createTask":
            payload = json.loads(request.content)
            assert payload["task"]["type"] == "HCaptchaClassification"
            assert payload["task"]["question"] == "click the cat"
            assert len(payload["task"]["queries"]) == 9
            # Queries and anchors MUST be base64-encoded strings, not raw URLs
            assert payload["task"]["queries"][0] == expected_b64
            assert payload["task"]["anchors"] == [expected_b64]

            return httpx.Response(
                200,
                json={
                    "errorId": 0,
                    "status": "ready",
                    "solution": {
                        "objects": [True, False, False, False, True, False, False, False, False]
                    },
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaBinaryReasoner(client=client)

        dummy_payload = CaptchaPayload(
            requester_question={"en": "click the cat"},
            requester_question_example=["https://example.com/cat_anchor.png"],
            tasklist=[
                CaptchaTask(datapoint_uri=f"https://example.com/img{i}.png")
                for i in range(9)
            ],
        )

        response = await reasoner(payload=dummy_payload)

    assert isinstance(response, ImageBinaryChallenge)
    assert response.challenge_prompt == "click the cat"
    assert len(response.coordinates) == 2
    assert response.coordinates[0].box_2d == [0, 0]
    assert response.coordinates[1].box_2d == [1, 1]

    # Test conversion back to boolean matrix
    matrix = response.convert_box_to_boolean_matrix()
    assert matrix == [True, False, False, False, True, False, False, False, False]

    # Test cache_response
    cache_file = tmp_path / "answer.json"
    reasoner.cache_response(cache_file)
    assert cache_file.exists()
    cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cached_data["challenge_prompt"] == "click the cat"


@pytest.mark.asyncio
async def test_binary_reasoner_with_fallback_screenshot(tmp_path):
    # Create a small dummy screenshot file
    img_path = tmp_path / "challenge_view.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert len(payload["task"]["queries"]) == 1
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {
                    "objects": [False, True, False, False, False, False, False, False, False]
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaBinaryReasoner(client=client)

        response = await reasoner(
            challenge_screenshot=img_path,
            question="Select dogs",
        )

    assert len(response.coordinates) == 1
    assert response.coordinates[0].box_2d == [0, 1]
    assert response.convert_box_to_boolean_matrix()[1] is True


def test_binary_label_solver_uses_yescaptcha_reasoner():
    from unittest.mock import MagicMock

    from hcaptcha_challenger.agent.config import AgentConfig
    from hcaptcha_challenger.agent.solvers.binary import BinaryLabelSolver

    config = AgentConfig(
        REASONING_PROVIDER="yescaptcha",
        YESCAPTCHA_CLIENT_KEY="test_key_xyz",
    )
    mock_driver = MagicMock()
    mock_pointer = MagicMock()

    solver = BinaryLabelSolver(config=config, driver=mock_driver, pointer=mock_pointer)
    assert isinstance(solver._image_classifier, YesCaptchaBinaryReasoner)


@pytest.mark.asyncio
async def test_binary_reasoner_raises_validation_error_when_solution_malformed(tmp_path):
    from pydantic import ValidationError

    img_path = tmp_path / "challenge_view.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")

    # Return solution missing 'objects'
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {},  # missing objects
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaBinaryReasoner(client=client)

        with pytest.raises(ValidationError):
            await reasoner(challenge_screenshot=img_path, question="Select dogs")


