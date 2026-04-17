# -*- coding: utf-8 -*-
"""
OpenRouterProvider - OpenRouter API implementation using OpenAI SDK.

This provider wraps the openai SDK connected to OpenRouter to provide image-based content generation.
"""
import base64
import json
from pathlib import Path
from typing import List, Type, TypeVar, Any

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed

ResponseT = TypeVar("ResponseT", bound=BaseModel)


def encode_image(image_path: Path) -> str:
    """Encode an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class OpenRouterProvider:
    """
    OpenRouter-based chat provider implementation.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key.
            model: Model name to use (e.g., "google/gemini-2.5-pro").
        """
        self._api_key = api_key
        self._model = model
        self._client: OpenAI | None = None
        self._response = None

    @property
    def client(self) -> OpenAI:
        """Lazy-initialize the OpenAI client pointed to OpenRouter."""
        if self._client is None:
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self._api_key,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry request ({retry_state.attempt_number}/3) - "
            f"Wait 3 seconds - Exception: {retry_state.outcome.exception()}"
        ),
    )
    def generate_with_images(
        self,
        *,
        images: List[Path],
        response_schema: Type[ResponseT],
        user_prompt: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> ResponseT:
        """
        Generate content with image inputs using OpenRouter.
        """
        actual_model = kwargs.pop("model", self._model)

        # Log which model is being used
        if actual_model != self._model:
            logger.debug(f"Using OpenRouter model override: {actual_model} (default: {self._model})")
        else:
            logger.debug(f"Using OpenRouter model: {actual_model}")

        content = []

        # Add images
        for img_path in images:
            if img_path and Path(img_path).exists():
                base64_img = encode_image(img_path)
                # Ensure we specify the correct mime type. Hardcoding jpeg works for most.
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        },
                    }
                )

        # Add user prompt
        if user_prompt:
            content.append(
                {
                    "type": "text",
                    "text": user_prompt
                }
            )

        messages = []
        if description:
            messages.append({"role": "system", "content": f"{description}\n\nIMPORTANT: You must return valid JSON that conforms to the required schema."})

        messages.append({"role": "user", "content": content})

        json_schema = response_schema.model_json_schema()

        # Generate response (sync)
        response = self.client.chat.completions.create(
            model=actual_model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": json_schema,
                    "strict": False
                }
            },
            **kwargs,
        )

        resp_content = response.choices[0].message.content
        if not resp_content:
            raise ValueError("Empty response from OpenRouter")
            
        try:
            self._response = response_schema.model_validate_json(resp_content)
        except Exception as e:
            # Fallback for models that wrap response in markdown
            if "```json" in resp_content:
                import re
                match = re.search(r"```json\s*([\s\S]*?)```", resp_content)
                if match:
                    json_str = match.group(1)
                    self._response = response_schema.model_validate_json(json_str)
                else:
                    raise e
            else:
                raise e

        # Extract stats if provided by OpenRouter
        if hasattr(response, 'usage') and response.usage:
            logger.debug(f"OpenRouter Usage: Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")

        return self._response

    def cache_response(self, path: Path) -> None:
        """Cache the last response to a file."""
        if self._response:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(
                        self._response.model_dump(mode="json"), indent=2, ensure_ascii=False
                    ),
                    encoding="utf-8",
                )
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")
