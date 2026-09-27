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


@pytest.mark.asyncio
async def test_client_dump_images(tmp_path):
    import base64

    # 1x1 transparent PNG base64
    sample_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errorId": 0, "status": "ready", "solution": {"objects": [True]}},
        )

    dump_dir = tmp_path / "yescaptcha_dumps"
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(
            client_key="test_key",
            client=http_client,
            dump_dir=dump_dir,
        )
        await client.create_task(
            task_type="HCaptchaClassification",
            question="Select cats",
            queries=[sample_b64, "https://example.com/cat2.png"],
            anchors=[sample_b64],
        )

    # Verify dump directory structure
    subfolders = list(dump_dir.glob("HCaptchaClassification_*"))
    assert len(subfolders) == 1
    task_folder = subfolders[0]

    assert (task_folder / "question.txt").exists()
    assert "Select cats" in (task_folder / "question.txt").read_text(encoding="utf-8")
    assert (task_folder / "query_0.png").exists()
    assert (task_folder / "query_0.png").read_bytes() == base64.b64decode(sample_b64)
    assert (task_folder / "query_1.url.txt").exists()
    assert "https://example.com/cat2.png" in (task_folder / "query_1.url.txt").read_text(encoding="utf-8")
    assert (task_folder / "anchor_0.png").exists()


@pytest.mark.asyncio
async def test_client_report_recent_tasks():
    reported_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/createTask":
            return httpx.Response(
                200,
                json={"errorId": 0, "status": "ready", "solution": {}, "taskId": "task_fail_1"},
            )
        elif request.url.path == "/report":
            payload = json.loads(request.content)
            reported_payloads.append(payload)
            return httpx.Response(200, json={"errorId": 0, "status": "success"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        
        # Execute a task
        await client.execute_task(
            task_type="HCaptchaClassification",
            question="select cars",
            queries=["car1"],
        )
        assert client.recent_task_ids == ["task_fail_1"]

        # Report as incorrect
        results = await client.report_recent_tasks(is_correct=False)
        assert len(results) == 1
        assert len(reported_payloads) == 1
        assert reported_payloads[0] == {
            "clientKey": "test_key",
            "id": "task_fail_1",
            "isSuccess": False,
            "taskId": "task_fail_1",
            "correct": False,
        }

        # Recent task IDs should now be cleared
        assert client.recent_task_ids == []


@pytest.mark.asyncio
async def test_client_clear_recent_tasks():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errorId": 0, "status": "ready", "solution": {}, "taskId": "task_pass_1"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = YesCaptchaClient(client_key="test_key", client=http_client)
        await client.execute_task(
            task_type="HCaptchaClassification",
            question="select cars",
            queries=["car1"],
        )
        assert client.recent_task_ids == ["task_pass_1"]
        client.clear_recent_tasks()
        assert client.recent_task_ids == []



