import base64
import json
import httpx
from pathlib import Path
from typing import List, TypeVar

from openai import AsyncOpenAI, APITimeoutError
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_not_exception_type
from loguru import logger
import asyncio

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
        self.model = model
        
        timeout_config = httpx.Timeout(timeout) if timeout is not None else httpx.USE_CLIENT_DEFAULT
        # Bắt buộc thêm provider-sticky-routing để tận dụng Prompt Caching của OpenRouter.
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout_config,
            default_headers={"provider-sticky-routing": "true"}
        )

    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_not_exception_type((APITimeoutError, asyncio.TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry OpenRouter request ({retry_state.attempt_number}/3) - "
            f"Wait 3 seconds - Exception: {retry_state.outcome.exception()}"
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

        # Filter out Gemini-specific kwargs if any, but usually we just pass valid OpenAI args
        # Pop thinking_level or other incompatible args if they arise.
        # For safety, let's keep it clean or assume caller uses standard args.
        call_kwargs = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        # Add additional compatible kwargs
        for k, v in kwargs.items():
            if k not in ["model", "messages", "response_format"]:
                call_kwargs[k] = v

        response = await self.client.chat.completions.create(**call_kwargs)

        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("Empty response from OpenRouter")

        try:
            parsed_json = json.loads(response_text)
            return response_schema(**parsed_json)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to parse or validate LLM response. Raw output: {response_text}")
            raise e
