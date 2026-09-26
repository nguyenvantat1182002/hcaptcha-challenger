# -*- coding: utf-8 -*-
import json
import pytest
import httpx

from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient
from hcaptcha_challenger.tools.yescaptcha.exceptions import (
    YesCaptchaError,
    YesCaptchaTaskError,
    YesCaptchaTimeoutError,
)


@pytest.mark.asyncio
async def test_client_create_task_immediate_ready():
    # Mock transport returning status=ready immediately
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/createTask"
        payload = json.loads(request.content)
        assert payload["clientKey"] == "test_key"
        assert payload["task"]["type"] == "HCaptchaClassification"
        assert payload["task"]["question"] == "select cats"

        return httpx.Response(
            200,
            json={
                "errorId": 0,
                "status": "ready",
                "solution": {"objects": [True, False, True]},
                "taskId": "task_123",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        result = await client.execute_task(
            task_type="HCaptchaClassification",
            question="select cats",
            queries=["cat1", "cat2", "cat3"],
        )

    assert result["objects"] == [True, False, True]


@pytest.mark.asyncio
async def test_client_create_task_polling_flow():
    # Mock transport returning processing first, then ready on poll
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/createTask":
            return httpx.Response(
                200,
                json={
                    "errorId": 0,
                    "status": "processing",
                    "taskId": "task_456",
                },
            )
        elif request.url.path == "/getTaskResult":
            payload = json.loads(request.content)
            assert payload["taskId"] == "task_456"
            if len(calls) == 2:
                return httpx.Response(200, json={"errorId": 0, "status": "processing"})
            else:
                return httpx.Response(
                    200,
                    json={
                        "errorId": 0,
                        "status": "ready",
                        "solution": {"clicks": [{"x": 100, "y": 200}]},
                    },
                )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(
            client_key="test_key",
            client=http_client,
            poll_interval=0.01,
            max_poll_attempts=5,
        )
        result = await client.execute_task(
            task_type="HCaptchaClassification",
            question="select area",
            queries=["img1"],
        )

    assert result["clicks"] == [{"x": 100, "y": 200}]
    assert calls == ["/createTask", "/getTaskResult", "/getTaskResult"]


@pytest.mark.asyncio
async def test_client_api_error_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "errorId": 1,
                "errorCode": "ERROR_KEY_DOES_NOT_EXIST",
                "errorDescription": "Client key not found",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="invalid_key", client=http_client)
        with pytest.raises(YesCaptchaTaskError) as exc_info:
            await client.execute_task(
                task_type="HCaptchaClassification",
                question="select cats",
                queries=["img1"],
            )

    assert "ERROR_KEY_DOES_NOT_EXIST" in str(exc_info.value)
    assert exc_info.value.error_id == 1


@pytest.mark.asyncio
async def test_client_polling_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/createTask":
            return httpx.Response(
                200,
                json={"errorId": 0, "status": "processing", "taskId": "timeout_task"},
            )
        return httpx.Response(200, json={"errorId": 0, "status": "processing"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(
            client_key="test_key",
            client=http_client,
            poll_interval=0.01,
            max_poll_attempts=2,
        )
        with pytest.raises(YesCaptchaTimeoutError):
            await client.execute_task(
                task_type="HCaptchaClassification",
                question="select cats",
                queries=["img1"],
            )


@pytest.mark.asyncio
async def test_client_report():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/report"
        payload = json.loads(request.content)
        assert payload["clientKey"] == "test_key"
        assert payload["taskId"] == 999
        assert payload["correct"] is True
        return httpx.Response(200, json={"errorId": 0, "status": "success"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        res = await client.report(task_id=999, is_correct=True)

    assert res["status"] == "success"


def test_client_default_headers_omit_manual_accept_encoding():
    from hcaptcha_challenger.tools.yescaptcha.client import DEFAULT_HEADERS

    # Ensuring accept-encoding is not manually overridden, so httpx handles decompression
    assert "accept-encoding" not in DEFAULT_HEADERS
    client = YesCaptchaClient(client_key="test_key")
    assert "accept-encoding" not in client._client.headers or client._client.headers["accept-encoding"] == "gzip, deflate"

