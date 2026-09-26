# -*- coding: utf-8 -*-
"""
Deep asynchronous YesCaptcha API client.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
import httpx
from loguru import logger
from pydantic import SecretStr

from hcaptcha_challenger.tools.yescaptcha.exceptions import (
    YesCaptchaError,
    YesCaptchaTaskError,
    YesCaptchaTimeoutError,
)

DEFAULT_HEADERS = {
    "sec-ch-ua": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
}


class YesCaptchaClient:
    """
    Asynchronous client for interacting with https://api.yescaptcha.com.

    Encapsulates connection pooling, payload formation, error mapping,
    and automatic task polling with backoff.
    """

    def __init__(
        self,
        client_key: str | SecretStr,
        base_url: str = "https://api.yescaptcha.com",
        timeout: float = 30.0,
        poll_interval: float = 1.0,
        max_poll_attempts: int = 30,
        client: httpx.AsyncClient | None = None,
    ):
        self._client_key = (
            client_key.get_secret_value() if isinstance(client_key, SecretStr) else client_key
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self.timeout,
        )

    async def __aenter__(self) -> YesCaptchaClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client session if owned internally."""
        if not self._external_client and not self._client.is_closed:
            await self._client.aclose()

    def _check_api_error(self, data: dict[str, Any]) -> None:
        error_id = data.get("errorId", 0)
        if error_id != 0:
            error_code = data.get("errorCode", "UNKNOWN_ERROR")
            description = data.get("errorDescription", str(data))
            raise YesCaptchaTaskError(
                f"YesCaptcha API error [{error_code}]: {description}",
                error_id=error_id,
                error_code=error_code,
                error_description=description,
            )

    async def create_task(
        self,
        task_type: str,
        question: str,
        queries: list[str] | str,
        anchors: list[str] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Creates a new solving task on YesCaptcha.
        """
        task_payload: dict[str, Any] = {
            "type": task_type,
            "question": question,
            "queries": queries,
            **extra,
        }
        if anchors:
            task_payload["anchors"] = anchors

        payload = {
            "clientKey": self._client_key,
            "task": task_payload,
        }

        url = f"{self.base_url}/createTask"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise YesCaptchaError(f"HTTP request to {url} failed: {e}") from e

        self._check_api_error(data)
        return data

    async def get_task_result(self, task_id: str | int) -> dict[str, Any]:
        """
        Fetches the current status and result for a created task.
        """
        payload = {
            "clientKey": self._client_key,
            "taskId": task_id,
        }

        url = f"{self.base_url}/getTaskResult"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise YesCaptchaError(f"HTTP request to {url} failed: {e}") from e

        self._check_api_error(data)
        return data

    async def wait_for_task_result(self, task_id: str | int) -> dict[str, Any]:
        """
        Polls getTaskResult with interval until the task status is 'ready'.
        """
        interval = self.poll_interval
        for attempt in range(1, self.max_poll_attempts + 1):
            await asyncio.sleep(interval)
            data = await self.get_task_result(task_id)
            status = data.get("status")

            if status == "ready":
                return data

            if status != "processing":
                raise YesCaptchaTaskError(
                    f"Unexpected task status: '{status}'",
                    error_description=str(data),
                )

            # Minor backoff up to 3s
            interval = min(interval * 1.25, 3.0)

        raise YesCaptchaTimeoutError(
            f"Exceeded {self.max_poll_attempts} poll attempts waiting for task {task_id}."
        )

    async def execute_task(
        self,
        task_type: str,
        question: str,
        queries: list[str] | str,
        anchors: list[str] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Convenience execution method: creates the task and waits for the solution.
        Returns the 'solution' dictionary directly.
        """
        initial_data = await self.create_task(
            task_type=task_type,
            question=question,
            queries=queries,
            anchors=anchors,
            **extra,
        )

        status = initial_data.get("status")
        if status == "ready":
            solution = initial_data.get("solution")
            if solution is None:
                raise YesCaptchaTaskError("Response was 'ready' but contained no solution.")
            return solution

        task_id = initial_data.get("taskId")
        if not task_id:
            raise YesCaptchaTaskError(
                f"Task status '{status}' without taskId in response: {initial_data}"
            )

        final_data = await self.wait_for_task_result(task_id)
        solution = final_data.get("solution")
        if solution is None:
            raise YesCaptchaTaskError("Final polled response contained no solution.")
        return solution

    async def report(self, task_id: str | int, is_correct: bool) -> dict[str, Any]:
        """
        Reports accuracy feedback for a solved task.
        """
        payload = {
            "clientKey": self._client_key,
            "taskId": task_id,
            "correct": is_correct,
        }

        url = f"{self.base_url}/report"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise YesCaptchaError(f"HTTP request to {url} failed: {e}") from e

        self._check_api_error(data)
        return data
