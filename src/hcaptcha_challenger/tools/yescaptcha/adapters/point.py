from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from hcaptcha_challenger.models import (
    CaptchaPayload,
    ChallengeImage,
    ImageAreaSelectChallenge,
    PointCoordinate,
)
from hcaptcha_challenger.tools.yescaptcha.adapters.base import (
    calculate_viewport_transform,
    resolve_image_to_base64,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient


class YesCaptchaClickItem(BaseModel):
    """Specific click coordinate returned by YesCaptcha."""

    x: float
    y: float


class YesCaptchaPointSolution(BaseModel):
    """Structured solution payload for point/area selection task."""

    clicks: list[YesCaptchaClickItem]


class YesCaptchaPointReasoner:
    """
    Adapter for area select challenges (IMAGE_LABEL_SINGLE_SELECT, IMAGE_LABEL_MULTI_SELECT).
    Conforms to Reasoner Seam and returns ImageAreaSelectChallenge.
    """

    requires_grid_projection: bool = False

    def __init__(self, client: YesCaptchaClient):
        self.client = client
        self._last_response: ImageAreaSelectChallenge | None = None

    def cache_response(self, path: Path) -> None:
        """Cache the last response to a file."""
        if not self._last_response:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_response.model_dump_json(indent=2))

    async def __call__(
        self,
        *,
        challenge_screenshot: ChallengeImage | bytes | str | Path,
        grid_divisions: str | Path | None = None,
        auxiliary_information: str | None = None,
        payload: CaptchaPayload | None = None,
        question: str | None = None,
        **kwargs: Any,
    ) -> ImageAreaSelectChallenge:
        # 1. Resolve question/prompt
        if question:
            q = question
        elif auxiliary_information:
            q = auxiliary_information
        elif payload:
            q = payload.get_requester_question()
        else:
            q = "Please select the requested points or areas."

        # 2. Queries and anchors (resolve remote URLs / ChallengeImage to raw base64)
        queries = [
            await resolve_image_to_base64(challenge_screenshot, http_client=self.client.http_client)
        ]
        anchors: list[str] | None = None
        if payload and payload.requester_question_example:
            ex = payload.requester_question_example
            raw_anchors = ex if isinstance(ex, list) else [ex]
            anchors = await asyncio.gather(*[
                resolve_image_to_base64(a, http_client=self.client.http_client)
                for a in raw_anchors
            ])

        logger.debug(f"[YesCaptchaPointReasoner] Executing task with prompt='{q}'")

        solution_dict = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
            anchors=anchors,
        )

        # Strongly-typed solution validation: 'clicks' must be explicitly present
        solution = YesCaptchaPointSolution.model_validate(solution_dict)

        # Calculate viewport coordinate transform
        offset_x, offset_y, scale_x, scale_y = calculate_viewport_transform(
            challenge_screenshot, kwargs.get("bbox")
        )

        points = [
            PointCoordinate(
                x=int(offset_x + click.x * scale_x),
                y=int(offset_y + click.y * scale_y),
            )
            for click in solution.clicks
        ]

        result = ImageAreaSelectChallenge(challenge_prompt=q, points=points)
        self._last_response = result
        return result
