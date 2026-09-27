"""
Deep asynchronous YesCaptcha API client.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path
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


def _dump_image_item(item: str, save_path: Path) -> None:
    """Save an image query or anchor item to disk (supports base64 and URL)."""
    try:
        if not isinstance(item, (str, bytes)):
            return
        # If it's a URL
        if isinstance(item, str) and item.startswith(("http://", "https://")):
            txt_path = save_path.with_suffix(".url.txt")
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            txt_path.write_text(item, encoding="utf-8")
        else:
            # Assume base64 string
            raw_str = item if isinstance(item, str) else item.decode("ascii")
            if "," in raw_str:
                raw_str = raw_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(raw_str)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(raw_bytes)
    except Exception as e:
        logger.warning(f"Failed to dump debug image to {save_path}: {e}")


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
        dump_dir: Path | str | None = Path("tmp/.yescaptcha_dumps"),
    ):
        self._client_key = (
            client_key.get_secret_value() if isinstance(client_key, SecretStr) else client_key
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self.dump_dir = Path(dump_dir) if dump_dir else None
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self.timeout,
        )
        self._recent_task_ids: list[str | int] = []

    @property
    def recent_task_ids(self) -> list[str | int]:
        """List of recent task IDs executed by this client."""
        return list(self._recent_task_ids)

    @property
    def http_client(self) -> httpx.AsyncClient:
        """The underlying httpx.AsyncClient instance."""
        return self._client

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
        # Dump images to disk if dump_dir is configured
        if self.dump_dir:
            try:
                task_folder = self.dump_dir.joinpath(f"{task_type}_{int(time.time() * 1000)}")
                task_folder.mkdir(parents=True, exist_ok=True)

                task_folder.joinpath("question.txt").write_text(
                    f"Type: {task_type}\nQuestion: {question}\n", encoding="utf-8"
                )

                query_list = queries if isinstance(queries, list) else [queries]
                for idx, q_item in enumerate(query_list):
                    _dump_image_item(q_item, task_folder.joinpath(f"query_{idx}.png"))

                if anchors:
                    anchor_list = anchors if isinstance(anchors, list) else [anchors]
                    for idx, a_item in enumerate(anchor_list):
                        _dump_image_item(a_item, task_folder.joinpath(f"anchor_{idx}.png"))
            except Exception as e:
                logger.warning(f"Error while dumping YesCaptcha task images: {e}")

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
        task_id = data.get("taskId")
        if task_id is not None:
            self._recent_task_ids.append(task_id)
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

    async def report_recent_tasks(self, is_correct: bool = False) -> list[dict[str, Any]]:
        """
        Reports feedback for all recently executed tasks and clears the recorded task IDs.
        """
        task_ids = list(self._recent_task_ids)
        self._recent_task_ids.clear()
        results = []
        for task_id in task_ids:
            try:
                res = await self.report(task_id=task_id, is_correct=is_correct)
                results.append(res)
                logger.info(
                    f"Reported YesCaptcha task {task_id} with correct={is_correct}"
                )
            except Exception as e:
                logger.warning(f"Failed to report YesCaptcha task {task_id}: {e}")
        return results

    def clear_recent_tasks(self) -> None:
        """
        Clears recent task IDs without reporting.
        """
        self._recent_task_ids.clear()
