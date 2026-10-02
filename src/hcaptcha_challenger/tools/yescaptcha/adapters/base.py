from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel

from hcaptcha_challenger.models import ChallengeImage


class ViewportBoundingBox(BaseModel):
    """Bounding box of the challenge view in viewport coordinates."""

    x: float
    y: float
    width: float
    height: float


async def resolve_image_to_base64(
    image: ChallengeImage | Path | str | bytes,
    http_client: httpx.AsyncClient,
) -> str:
    """Resolve an in-memory ChallengeImage, file Path, bytes, or remote asset URL to a raw Base64 string."""
    if isinstance(image, ChallengeImage):
        return image.as_base64

    if isinstance(image, Path):
        return ChallengeImage.from_file(image).as_base64

    if isinstance(image, (bytes, bytearray)):
        return base64.b64encode(image).decode("utf-8")

    if isinstance(image, str):
        if image.startswith(("http://", "https://")):
            resp = await http_client.get(image)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        return image

    raise TypeError(f"Unsupported image type: {type(image)}")


def calculate_viewport_transform(
    challenge_screenshot: ChallengeImage | bytes | str | Path,
    bbox: ViewportBoundingBox | dict[str, Any] | None,
) -> tuple[float, float, float, float]:
    """
    Calculate coordinate translation and scaling factors from challenge image space
    to browser viewport space.

    Returns:
        tuple of (offset_x, offset_y, scale_x, scale_y)
    """
    if bbox is None:
        return 0.0, 0.0, 1.0, 1.0

    box = (
        bbox if isinstance(bbox, ViewportBoundingBox) else ViewportBoundingBox.model_validate(bbox)
    )
    offset_x = box.x
    offset_y = box.y
    scale_x = 1.0
    scale_y = 1.0

    try:
        img = (
            challenge_screenshot
            if isinstance(challenge_screenshot, ChallengeImage)
            else (
                ChallengeImage.from_bytes(challenge_screenshot)
                if isinstance(challenge_screenshot, (bytes, bytearray))
                else ChallengeImage.from_file(challenge_screenshot)
            )
        )
        img_w, img_h = img.dimensions

        if img_w > 0 and img_h > 0:
            scale_x = box.width / img_w
            scale_y = box.height / img_h
    except (OSError, ValueError) as e:
        logger.warning(f"Could not inspect image dimensions for scaling: {e}")

    return offset_x, offset_y, scale_x, scale_y
