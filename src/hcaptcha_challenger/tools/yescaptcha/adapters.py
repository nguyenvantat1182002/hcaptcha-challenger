# -*- coding: utf-8 -*-
"""
YesCaptcha reasoner adapters conforming to the Reasoner Seam.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from loguru import logger

from hcaptcha_challenger.models import (
    BoundingBoxCoordinate,
    CaptchaPayload,
    ImageAreaSelectChallenge,
    ImageBinaryChallenge,
    ImageDragDropChallenge,
    PointCoordinate,
    SpatialPath,
)
from hcaptcha_challenger.tools.yescaptcha.client import YesCaptchaClient


def encode_image_to_base64(image_path: str | Path) -> str:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found at path: {path}")
    raw_bytes = path.read_bytes()
    return base64.b64encode(raw_bytes).decode("utf-8")


class YesCaptchaBinaryReasoner:
    """
    Adapter for 9-grid binary image classification using YesCaptcha.
    Conforms to the Reasoner Seam and returns ImageBinaryChallenge.
    """

    def __init__(self, client: YesCaptchaClient):
        self.client = client
        self._last_response: ImageBinaryChallenge | None = None

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
        challenge_screenshot: str | Path | None = None,
        payload: CaptchaPayload | None = None,
        question: str | None = None,
        **kwargs: Any,
    ) -> ImageBinaryChallenge:
        # 1. Resolve challenge question
        if question:
            q = question
        elif payload:
            q = payload.get_requester_question()
        else:
            q = "Please click each image containing the requested object."

        # 2. Resolve queries
        queries: list[str] = []
        if payload and payload.tasklist:
            queries = [
                task.datapoint_uri
                for task in payload.tasklist
                if task.datapoint_uri
            ]

        if not queries:
            if not challenge_screenshot:
                raise ValueError("Neither payload with tasklist nor challenge_screenshot provided.")
            queries = [encode_image_to_base64(challenge_screenshot)]

        # 3. Resolve anchors
        anchors: list[str] | None = None
        if payload and payload.requester_question_example:
            example = payload.requester_question_example
            if isinstance(example, list):
                anchors = [str(x) for x in example]
            elif isinstance(example, str):
                anchors = [example]

        logger.debug(f"[YesCaptchaBinaryReasoner] Executing task with question='{q}', {len(queries)} queries")

        solution = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
            anchors=anchors,
        )

        objects: list[bool] = solution.get("objects", [])

        # Map 1D boolean array to 2D coordinates [row, col]
        coordinates: list[BoundingBoxCoordinate] = []
        for i, is_target in enumerate(objects):
            if is_target:
                row = i // 3
                col = i % 3
                coordinates.append(BoundingBoxCoordinate(box_2d=[row, col]))

        result = ImageBinaryChallenge(challenge_prompt=q, coordinates=coordinates)
        self._last_response = result
        return result


class YesCaptchaPointReasoner:
    """
    Adapter for area select challenges (IMAGE_LABEL_SINGLE_SELECT, IMAGE_LABEL_MULTI_SELECT).
    Conforms to Reasoner Seam and returns ImageAreaSelectChallenge.
    """

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
        challenge_screenshot: str | Path,
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

        # 2. Queries and anchors
        queries = [encode_image_to_base64(challenge_screenshot)]
        anchors: list[str] | None = None
        if payload and payload.requester_question_example:
            ex = payload.requester_question_example
            anchors = [str(x) for x in ex] if isinstance(ex, list) else [str(ex)]

        logger.debug(f"[YesCaptchaPointReasoner] Executing task with prompt='{q}'")

        solution = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
            anchors=anchors,
        )

        clicks = solution.get("clicks", [])
        points = [
            PointCoordinate(x=int(c["x"]), y=int(c["y"]))
            for c in clicks
            if "x" in c and "y" in c
        ]

        result = ImageAreaSelectChallenge(challenge_prompt=q, points=points)
        self._last_response = result
        return result


class YesCaptchaPathReasoner:
    """
    Adapter for drag-and-drop challenges (IMAGE_DRAG_SINGLE, IMAGE_DRAG_MULTI).
    Conforms to Reasoner Seam and returns ImageDragDropChallenge.
    """

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
        challenge_screenshot: str | Path,
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
        queries = [encode_image_to_base64(challenge_screenshot)]

        logger.debug(f"[YesCaptchaPathReasoner] Executing task with prompt='{q}'")

        solution = await self.client.execute_task(
            task_type="HCaptchaClassification",
            question=q,
            queries=queries,
        )

        boxes = solution.get("box", [])
        paths: list[SpatialPath] = []
        for box in boxes:
            start = box.get("start", [0, 0])
            end = box.get("end", [0, 0])
            paths.append(
                SpatialPath(
                    start_point=PointCoordinate(x=int(start[0]), y=int(start[1])),
                    end_point=PointCoordinate(x=int(end[0]), y=int(end[1])),
                )
            )

        result = ImageDragDropChallenge(challenge_prompt=q, paths=paths)
        self._last_response = result
        return result
