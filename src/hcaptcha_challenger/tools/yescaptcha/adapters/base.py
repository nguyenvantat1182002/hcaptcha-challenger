from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image
from pydantic import BaseModel


class ViewportBoundingBox(BaseModel):
    """Bounding box of the challenge view in viewport coordinates."""

    x: float
    y: float
    width: float
    height: float


def encode_image_to_base64(image_path: str | Path) -> str:
    """Encode an image file to a base64 UTF-8 string."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found at path: {path}")
    raw_bytes = path.read_bytes()
    return base64.b64encode(raw_bytes).decode("utf-8")


def calculate_viewport_transform(
    challenge_screenshot: str | Path,
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

    box = bbox if isinstance(bbox, ViewportBoundingBox) else ViewportBoundingBox.model_validate(bbox)
    offset_x = box.x
    offset_y = box.y
    scale_x = 1.0
    scale_y = 1.0

    try:
        with Image.open(challenge_screenshot) as img:
            img_w, img_h = img.size
            if img_w > 0 and img_h > 0:
                scale_x = box.width / img_w
                scale_y = box.height / img_h
    except (OSError, ValueError) as e:
        logger.warning(f"Could not inspect image dimensions for scaling: {e}")

    return offset_x, offset_y, scale_x, scale_y
