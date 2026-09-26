from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from hcaptcha_challenger.models import (
    CaptchaPayload,
    ChallengeImage,
    ImageDragDropChallenge,
    PointCoordinate,
    SpatialPath,
)
from hcaptcha_challenger.tools.yescaptcha.adapters.base import (
    calculate_viewport_transform,
    resolve_image_to_base64,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient


class YesCaptchaBoxItem(BaseModel):
    """Specific drag path box coordinates returned by YesCaptcha."""

    start: tuple[float, float]
    end: tuple[float, float]


class YesCaptchaPathSolution(BaseModel):
    """Structured solution payload for drag-and-drop task."""

    box: list[YesCaptchaBoxItem]


class YesCaptchaPathReasoner:
    """
    Adapter for drag-and-drop challenges (IMAGE_DRAG_SINGLE, IMAGE_DRAG_MULTI).
    Conforms to Reasoner Seam and returns ImageDragDropChallenge.
    """

    requires_grid_projection: bool = False

    def __init__(self, client: YesCaptchaClient):
        self.client = client
        self._last_response: ImageDragDropChallenge | None = None

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
    ) -> ImageDragDropChallenge:
        # 1. Resolve question/prompt
        if question:
            q = question
        elif auxiliary_information:
            q = auxiliary_information
        elif payload:
            q = payload.get_requester_question()
        else:
            q = "Please drag the puzzle piece to the target location."

        # 2. Queries
        queries = [
            await resolve_image_to_base64(challenge_screenshot, http_client=self.client.http_client)
        ]

        logger.debug(f"[YesCaptchaPathReasoner] Executing task with prompt='{q}'")

        solution_dict = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
        )

        # Strongly-typed solution validation: 'box' must be explicitly present with [start, end]
        solution = YesCaptchaPathSolution.model_validate(solution_dict)

        # Calculate viewport coordinate transform
        offset_x, offset_y, scale_x, scale_y = calculate_viewport_transform(
            challenge_screenshot, kwargs.get("bbox")
        )

        paths: list[SpatialPath] = [
            SpatialPath(
                start_point=PointCoordinate(
                    x=int(offset_x + item.start[0] * scale_x),
                    y=int(offset_y + item.start[1] * scale_y),
                ),
                end_point=PointCoordinate(
                    x=int(offset_x + item.end[0] * scale_x),
                    y=int(offset_y + item.end[1] * scale_y),
                ),
            )
            for item in solution.box
        ]

        result = ImageDragDropChallenge(challenge_prompt=q, paths=paths)
        self._last_response = result
        return result
