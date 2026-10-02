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
    ViewportBoundingBox,
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
        path.write_text(self._last_response.model_dump_json(indent=2), encoding="utf-8")

    async def __call__(
        self,
        *,
        challenge_screenshot: ChallengeImage | bytes | str | Path,
        grid_divisions: str | Path | None = None,
        auxiliary_information: str | None = None,
        payload: CaptchaPayload | None = None,
        question: str | None = None,
        bbox: ViewportBoundingBox | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ImageDragDropChallenge:
        q = (
            question
            or auxiliary_information
            or (payload.get_requester_question() if payload else None)
            or "Please drag the puzzle piece to the target location."
        )

        queries = [
            await resolve_image_to_base64(challenge_screenshot, http_client=self.client.http_client)
        ]

        logger.debug(f"[YesCaptchaPathReasoner] Executing task with prompt='{q}'")

        solution_dict = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
        )

        solution = YesCaptchaPathSolution.model_validate(solution_dict)

        offset_x, offset_y, scale_x, scale_y = calculate_viewport_transform(
            challenge_screenshot, bbox
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
