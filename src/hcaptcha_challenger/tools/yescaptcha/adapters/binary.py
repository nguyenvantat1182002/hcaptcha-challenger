import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from hcaptcha_challenger.models import (
    BoundingBoxCoordinate,
    CaptchaPayload,
    ChallengeImage,
    ImageBinaryChallenge,
)
from hcaptcha_challenger.tools.yescaptcha.adapters.base import (
    resolve_image_to_base64,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient


class YesCaptchaBinarySolution(BaseModel):
    """Structured solution payload for binary classification task."""

    objects: list[bool]


class YesCaptchaBinaryReasoner:
    """
    Adapter for 9-grid binary image classification using YesCaptcha.
    Conforms to the Reasoner Seam and returns ImageBinaryChallenge.
    """

    requires_grid_projection: bool = False

    def __init__(self, client: YesCaptchaClient):
        self.client = client
        self._last_response: ImageBinaryChallenge | None = None

    def cache_response(self, path: Path) -> None:
        """Cache the last response to a file."""
        if not self._last_response:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._last_response.model_dump_json(indent=2), encoding="utf-8")

    async def __call__(
        self,
        *,
        challenge_screenshot: ChallengeImage | bytes | str | Path | None = None,
        payload: CaptchaPayload | None = None,
        question: str | None = None,
        **kwargs: Any,
    ) -> ImageBinaryChallenge:
        q = (
            question
            or (payload.get_requester_question() if payload else None)
            or "Please click each image containing the requested object."
        )

        raw_queries: list[Any] = []
        if payload and payload.tasklist:
            raw_queries = [
                task.datapoint_uri for task in payload.tasklist if task.datapoint_uri
            ]

        if not raw_queries:
            if not challenge_screenshot:
                raise ValueError(
                    "Neither payload with tasklist nor challenge_screenshot provided."
                )
            raw_queries = [challenge_screenshot]

        queries = await asyncio.gather(
            *[
                resolve_image_to_base64(query_item, http_client=self.client.http_client)
                for query_item in raw_queries
            ]
        )

        anchors: list[str] | None = None
        if payload and payload.requester_question_example:
            example = payload.requester_question_example
            raw_anchors = example if isinstance(example, list) else [example]
            anchors = await asyncio.gather(
                *[
                    resolve_image_to_base64(a, http_client=self.client.http_client)
                    for a in raw_anchors
                ]
            )

        logger.debug(
            f"[YesCaptchaBinaryReasoner] Executing task with question='{q}', {len(queries)} queries"
        )

        solution_dict = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
            anchors=anchors,
        )

        solution = YesCaptchaBinarySolution.model_validate(solution_dict)

        # 3x3 grid index mapping: row = index // 3, col = index % 3
        coordinates = [
            BoundingBoxCoordinate(box_2d=[i // 3, i % 3])
            for i, is_target in enumerate(solution.objects)
            if is_target
        ]

        result = ImageBinaryChallenge(challenge_prompt=q, coordinates=coordinates)
        self._last_response = result
        return result
