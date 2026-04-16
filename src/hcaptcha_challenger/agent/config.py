import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SecretStr
from pathlib import Path
from typing import Any, List
from datetime import datetime
from loguru import logger

from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.models import CoordinateGrid
from hcaptcha_challenger.models import (
    SCoTModelType,
    RequestType,
    DEFAULT_SCOT_MODEL,
    DEFAULT_FAST_SHOT_MODEL,
    FastShotModelType,
    CaptchaPayload,
    INV,
    IGNORE_REQUEST_TYPE_LITERAL
)


SINGLE_IGNORE_TYPE = IGNORE_REQUEST_TYPE_LITERAL | RequestType | ChallengeTypeEnum
IGNORE_REQUEST_TYPE_LIST = List[SINGLE_IGNORE_TYPE]


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    GEMINI_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("GEMINI_API_KEY", "")),
        description="Create API Key https://aistudio.google.com/app/apikey",
    )

    cache_dir: Path = Path("tmp/.cache")
    challenge_dir: Path = Path("tmp/.challenge")
    captcha_response_dir: Path = Path("tmp/.captcha")
    ignore_request_types: IGNORE_REQUEST_TYPE_LIST | None = Field(default_factory=list)
    ignore_request_questions: List[str] | None = Field(default_factory=list)
    
    MOUSE_SPEED: float = Field(
        default=1.0,
        description="Mouse movement speed multiplier. "
        "0.5 = fast (2x speed), 1.0 = normal, 2.0 = slow (half speed). "
        "Affects both per-point delay and burst pauses.",
    )

    DISABLE_HSW_REVERSE: bool = Field(
        default=False,
        description="Force disable HSW reverse engineering and fallback to visual recognition. "
        "Useful for testing the fallback branch when HSW decoding fails.",
    )

    MAX_CRUMB_COUNT: int = Field(
        default=2,
        description="""
        CRUMB_COUNT: The number of challenge rounds you need to solve once the challenge starts.
        In the vast majority of cases this value will be 2, some specialized sites will set this value to 3.
        In most cases you don't need to change this value, the `_review_challenge_type` task determines the exact value of `CRUMB_COUNT` based on the information of the assigned task.
        Only manually change this value if you are working on a very specific task that prevents the `_review_challenge_type` from hijacking the task information and the maximum number of tasks > 2.
        """,
    )

    EXECUTION_TIMEOUT: float = Field(
        default=120,
        description="When your local network is poor, increase this value appropriately [unit: second]",
    )
    RESPONSE_TIMEOUT: float = Field(
        default=30,
        description="When your local network is poor, increase this value appropriately [unit: second]",
    )
    WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS: int = Field(
        default=1500,
        description="When your local network is poor, increase this value appropriately [unit: millisecond]",
    )

    CHALLENGE_CLASSIFIER_MODEL: FastShotModelType = Field(
        default=DEFAULT_FAST_SHOT_MODEL,
        description="For the challenge classification task \n"
        "Used as last resort when HSW decoding fails.",
    )
    IMAGE_CLASSIFIER_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL, description="For the challenge type: `image_label_binary`"
    )
    SPATIAL_POINT_REASONER_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL,
        description="For the challenge type: `image_label_area_select` (single/multi)",
    )
    SPATIAL_PATH_REASONER_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL,
        description="For the challenge type: `image_drag_drop` (single/multi)",
    )

    coordinate_grid: CoordinateGrid | None = Field(default_factory=CoordinateGrid)

    enable_challenger_debug: bool | None = Field(default=False, description="Enable debug mode")

    # == Skills Configuration == #
    custom_skills_path: Path | None = Field(
        default=None, description="Path to custom skills rules.yaml"
    )
    enable_skills_update: bool = Field(
        default=False, description="Enable auto-update of skills from GitHub"
    )
    skills_update_repo: str = Field(
        default="QIN2DIM/hcaptcha-challenger", description="GitHub repo for skills update"
    )
    skills_update_branch: str = Field(default="main", description="GitHub branch for skills update")

    @field_validator('GEMINI_API_KEY', mode="before")
    @classmethod
    def validate_api_key(cls, v: Any) -> str:
        """
        Validates that the GEMINI_API_KEY is not empty.

        Args:
            v: The API key value to validate

        Returns:
            The validated API key

        Raises:
            ValueError: If the API key is empty
        """
        if not v or not isinstance(v, str):
            raise ValueError(
                "GEMINI_API_KEY is required but not provided. "
                "Please either pass it directly or set the GEMINI_API_KEY environment variable."
                "Create API Key -> https://aistudio.google.com/app/apikey"
            )
        return v

    @property
    def spatial_grid_cache(self):
        return self.cache_dir.joinpath("spatial_grid")

    def create_cache_key(
        self,
        captcha_payload: CaptchaPayload | None = None,
        request_type: str = "type",
        prompt: str = "unknown",
    ) -> Path:
        """

        Args:
            captcha_payload:
            request_type:
            prompt:

        Returns: ./.challenge / require_type / prompt / current_time

        """
        current_datetime = datetime.now()
        current_time = current_datetime.strftime("%Y%m%d/%Y%m%d%H%M%S%f")

        prompt = prompt.translate(str.maketrans("", "", "".join(INV)))

        if not captcha_payload:
            _cache_key_temp = self.challenge_dir.joinpath(request_type, prompt, current_time)
            if self.enable_challenger_debug:
                logger.debug(f"Create cache-key [NotCaptchaPayload] - {_cache_key_temp.resolve()}")
            return _cache_key_temp

        cache_key = self.challenge_dir.joinpath(
            captcha_payload.request_type.value,
            captcha_payload.get_requester_question(),
            current_time,
        )

        try:
            _cache_path_captcha = cache_key.joinpath(f"{cache_key.name}_captcha.json")
            _cache_path_captcha.parent.mkdir(parents=True, exist_ok=True)

            _unpacked_data = captcha_payload.model_dump(mode="json")
            _cache_path_captcha.write_text(
                json.dumps(_unpacked_data, indent=2, ensure_ascii=False), encoding="utf8"
            )
        except Exception as e:
            logger.error(f"Failed to write captcha payload to cache: {e}")

        if self.enable_challenger_debug:
            logger.debug(f"Create cache-key [Direct] - {cache_key.resolve()}")

        return cache_key