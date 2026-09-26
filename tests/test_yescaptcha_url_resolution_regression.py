import base64
import json

import httpx
import pytest

from hcaptcha_challenger.models import (
    CaptchaPayload,
    CaptchaTask,
    ChallengeImage,
    ImageAreaSelectChallenge,
    ImageBinaryChallenge,
)
from hcaptcha_challenger.tools.yescaptcha.adapters import (
    YesCaptchaBinaryReasoner,
    YesCaptchaPointReasoner,
)
from hcaptcha_challenger.tools.yescaptcha.adapters.base import (
    resolve_image_to_base64,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient

SAMPLE_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
SAMPLE_PNG_BASE64 = base64.b64encode(SAMPLE_PNG_BYTES).decode("utf-8")


@pytest.mark.asyncio
async def test_resolve_image_to_base64_varieties():
    def url_handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://example.com/test.png")
        return httpx.Response(200, content=SAMPLE_PNG_BYTES)

    async with httpx.AsyncClient(transport=httpx.MockTransport(url_handler)) as http_client:
        # 1. In-memory ChallengeImage
        img = ChallengeImage.from_bytes(SAMPLE_PNG_BYTES)
        assert await resolve_image_to_base64(img, http_client) == SAMPLE_PNG_BASE64

        # 2. Remote HTTP URL
        b64 = await resolve_image_to_base64("https://example.com/test.png", http_client)
        assert b64 == SAMPLE_PNG_BASE64

        # 3. Already a raw base64 string
        assert await resolve_image_to_base64(SAMPLE_PNG_BASE64, http_client) == SAMPLE_PNG_BASE64



@pytest.mark.asyncio
async def test_binary_reasoner_resolves_urls_to_base64():
    """
    Regression test for user issue:
    Verifies that YesCaptchaBinaryReasoner automatically downloads remote datapoint_uri
    and requester_question_example URLs and converts them to valid raw Base64 strings.
    """
    def mock_handler(request: httpx.Request) -> httpx.Response:
        # 1. If it's a remote asset download from CDN
        if "hcaptcha.com" in request.url.host:
            return httpx.Response(200, content=SAMPLE_PNG_BYTES)

        # 2. If it's the YesCaptcha createTask API
        if request.url.path == "/createTask":
            body = json.loads(request.content)
            task = body.get("task", {})
            queries = task.get("queries", [])
            anchors = task.get("anchors", [])

            # Assert strictly: NO URL should be forwarded to YesCaptcha API
            for q in queries:
                assert not q.startswith("http"), f"Found raw URL in queries: {q}"
                assert not q.startswith("data:"), f"Found data URI in queries: {q}"
                decoded = base64.b64decode(q, validate=True)
                assert decoded == SAMPLE_PNG_BYTES

            for a in anchors:
                assert not a.startswith("http"), f"Found raw URL in anchors: {a}"
                assert not a.startswith("data:"), f"Found data URI in anchors: {a}"
                decoded = base64.b64decode(a, validate=True)
                assert decoded == SAMPLE_PNG_BYTES

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

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaBinaryReasoner(client=client)

        payload = CaptchaPayload(
            requester_question={"en": "Select all items that are typically used with the shown item"},
            requester_question_example=["https://imgs.hcaptcha.com/anchor_example.png"],
            tasklist=[
                CaptchaTask(datapoint_uri=f"https://imgs.hcaptcha.com/tile_{i}.jpeg")
                for i in range(9)
            ],
        )

        response = await reasoner(payload=payload)

        assert isinstance(response, ImageBinaryChallenge)
        assert response.challenge_prompt == "Select all items that are typically used with the shown item"
        assert len(response.coordinates) == 2
        assert response.coordinates[0].box_2d == [0, 0]
        assert response.coordinates[1].box_2d == [1, 1]


@pytest.mark.asyncio
async def test_point_reasoner_resolves_anchor_url_to_base64():
    """
    Regression test ensuring YesCaptchaPointReasoner also downloads and base64-encodes
    requester_question_example anchors before sending to YesCaptcha.
    """
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if "hcaptcha.com" in request.url.host:
            return httpx.Response(200, content=SAMPLE_PNG_BYTES)

        if request.url.path == "/createTask":
            body = json.loads(request.content)
            task = body.get("task", {})
            anchors = task.get("anchors", [])

            assert len(anchors) == 1
            assert not anchors[0].startswith("http")
            decoded = base64.b64decode(anchors[0], validate=True)
            assert decoded == SAMPLE_PNG_BYTES

            return httpx.Response(
                200,
                json={
                    "errorId": 0,
                    "status": "ready",
                    "solution": {
                        "clicks": [{"x": 100, "y": 150}]
                    },
                },
            )

        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        reasoner = YesCaptchaPointReasoner(client=client)

        payload = CaptchaPayload(
            requester_question={"en": "Click on the center of the apple"},
            requester_question_example=["https://imgs.hcaptcha.com/example_apple.png"],
        )

        challenge_image = ChallengeImage.from_bytes(SAMPLE_PNG_BYTES)
        response = await reasoner(
            challenge_screenshot=challenge_image,
            payload=payload,
        )

        assert isinstance(response, ImageAreaSelectChallenge)
        assert len(response.points) == 1
        assert response.points[0].x == 100
        assert response.points[0].y == 150
