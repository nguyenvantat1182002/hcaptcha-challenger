import base64
import json
import httpx
from pathlib import Path
from typing import List, TypeVar, Optional

from openai import AsyncOpenAI, APITimeoutError, RateLimitError
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from loguru import logger
import asyncio
import os
import time

ResponseT = TypeVar("ResponseT", bound=BaseModel)

class OpenRouterProvider:
    """
    OpenRouter implementation of the ChatProvider protocol.
    Provides structured JSON outputs using response_format={"type": "json_object"}
    """

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini", timeout: float | None = None):
        """
        Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key.
            model: Model identifier.
            timeout: Optional LLM HTTP timeout.
        """
        self.api_key = api_key
        
        fallback_env = os.getenv("OPENROUTER_FALLBACK_MODELS", "").strip()
        self.fallback_models = [m.strip() for m in fallback_env.split(",")] if fallback_env else []
        self.model = self.fallback_models[0] if self.fallback_models else model

        self._local_request_count = 0
        self._rate_limit_requests: Optional[int] = None
        self._ipc_file = Path(".openrouter_ratelimit")
        
        self._rate_limit_fetched = False
        
        timeout_config = httpx.Timeout(timeout) if timeout is not None else httpx.Timeout(120.0)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout_config,
            default_headers={"provider-sticky-routing": "true"}
        )

    async def _fetch_api_rate_limits(self, update_lock: bool = False):
        """Fetch rate limits from OpenRouter API. Updates limit config and optionally writes IPC lock."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {self.api_key}"})
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    rate_limit = data.get("rate_limit", {})
                    if rate_limit:
                        # 1. Update base limits (for init)
                        req_limit = rate_limit.get("requests")
                        if req_limit and req_limit > 0:
                            self._rate_limit_requests = req_limit
                            
                        # 2. Write lock file (if triggered by 429 or 70% threshold)
                        if update_lock:
                            interval_str = rate_limit.get("interval", "10s")
                            try:
                                if interval_str.endswith("s"):
                                    wait_s = float(interval_str[:-1])
                                elif interval_str.endswith("m"):
                                    wait_s = float(interval_str[:-1]) * 60
                                else:
                                    wait_s = 10.0
                            except ValueError:
                                wait_s = 10.0
                            
                            reset_time = time.time() + wait_s
                            with open(self._ipc_file, "w") as f:
                                f.write(str(reset_time))
        except Exception as e:
            logger.warning(f"Failed to fetch rate limit from /auth/key: {e}")

    async def _check_ipc_lock_and_sleep(self):
        """Check if IPC lock file exists and sleep if active."""
        if self._ipc_file.exists():
            try:
                with open(self._ipc_file, "r") as f:
                    reset_epoch = float(f.read().strip())
                current = time.time()
                if current < reset_epoch:
                    wait_time = reset_epoch - current
                    logger.info(f"IPC Lock active. Proactive sleep for {wait_time:.2f}s.")
                    await asyncio.sleep(wait_time)
                else:
                    self._ipc_file.unlink(missing_ok=True)
            except Exception:
                pass

    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_not_exception_type((APITimeoutError, asyncio.TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry OpenRouter request ({retry_state.attempt_number}/5) - "
            f"Wait {retry_state.next_action.sleep}s - Exception: {retry_state.outcome.exception()}"
        ),
    )
    async def generate_with_images(
        self,
        *,
        images: List[Path],
        response_schema: type[ResponseT],
        user_prompt: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> ResponseT:
        """
        Generate content with image inputs and map to response_schema.
        """
        await self._check_ipc_lock_and_sleep()
        
        if not self._rate_limit_fetched:
            await self._fetch_api_rate_limits(update_lock=False)
            self._rate_limit_fetched = True
        
        self._local_request_count += 1
        if self._rate_limit_requests and self._local_request_count >= self._rate_limit_requests * 0.7:
            logger.info("Local request count reached 70% threshold. Fetching reset time and locking.")
            await self._fetch_api_rate_limits(update_lock=True)
            self._local_request_count = 0
            await self._check_ipc_lock_and_sleep()

        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        system_instruction = description or "You are a helpful assistant."
        system_instruction += (
            "\n\nYou MUST return a valid JSON object adhering exactly to this JSON Schema:\n"
            f"{schema_json}\n\n"
            "Do not return markdown formatting blocks like ```json, just the raw JSON object."
        )

        messages = [{"role": "system", "content": system_instruction}]

        content_list = []
        if user_prompt:
            content_list.append({"type": "text", "text": user_prompt})

        for img_path in images:
            base64_image = self._encode_image(img_path)
            content_list.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )

        messages.append({"role": "user", "content": content_list})

        call_kwargs = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        
        if self.fallback_models:
            call_kwargs["extra_body"] = {"models": self.fallback_models}

        for k, v in kwargs.items():
            if k not in ["model", "messages", "response_format", "extra_body"]:
                call_kwargs[k] = v

        try:
            response = await self.client.chat.completions.create(**call_kwargs)
        except RateLimitError as e:
            # Nếu vô tình gặp 429 (do nhiều process đẩy cùng lúc), ta sẽ lấy lại limit bằng API thay vì đọc Header
            logger.warning("Hit 429 RateLimitError. Fetching limits from API to update lock.")
            await self._fetch_api_rate_limits(update_lock=True)

            # Re-raise so tenacity handles the retry and sleep
            raise e

        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("Empty response from OpenRouter")

        try:
            parsed_json = json.loads(response_text)
            return response_schema(**parsed_json)
        except Exception as e:
            logger.error(f"Failed to parse or validate LLM response. Raw output: {response_text}")
            raise e
