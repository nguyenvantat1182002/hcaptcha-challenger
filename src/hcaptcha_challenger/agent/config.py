import json
from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hcaptcha_challenger.models import (
    RequestType,
    SCoTModelType,
    DEFAULT_SCOT_MODEL,
    DEFAULT_FAST_SHOT_MODEL,
    FastShotModelType,
    CaptchaPayload,
    IGNORE_REQUEST_TYPE_LITERAL,
    INV,
    ChallengeTypeEnum,
    CoordinateGrid,
)

SINGLE_IGNORE_TYPE = IGNORE_REQUEST_TYPE_LITERAL | RequestType | ChallengeTypeEnum
IGNORE_REQUEST_TYPE_LIST = List[SINGLE_IGNORE_TYPE]


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    GEMINI_API_KEY: SecretStr | None = Field(
        default=None,
        description="Create API Key https://aistudio.google.com/app/apikey",
    )
    OPENROUTER_API_KEY: SecretStr | None = Field(
        default=None,
        description="Create API Key https://openrouter.ai/keys",
    )

    cache_dir: Path = Path("tmp/.cache")
    challenge_dir: Path = Path("tmp/.challenge")
    captcha_response_dir: Path = Path("tmp/.captcha")
    ignore_request_types: IGNORE_REQUEST_TYPE_LIST | None = Field(default_factory=list)
    ignore_request_questions: List[str] | None = Field(default_factory=list)

    ENABLE_CAPTCHA_CACHE: bool = Field(
        default=True,
        description="Enable saving validated captcha responses to local cache files.",
    )

    DISABLE_BEZIER_TRAJECTORY: bool = Field(
        default=False,
        description="If you use Camoufox, it is recommended to turn off "
        "the custom Bessel track generator of hcaptcha-challenger "
        "and use Camoufox(humanize=True)",
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
    LLM_TIMEOUT: float = Field(
        default=120.0,
        description="LLM HTTP timeout in seconds (Set higher if OpenRouter queues) [unit: second]",
    )
    RETRY_ON_FAILURE: bool = Field(
        default=False, description="Re-execute the challenge when it fails"
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
        default=DEFAULT_SCOT_MODEL,
        description="For the challenge type: `image_label_binary`",
    )
    SPATIAL_POINT_REASONER_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL,
        description="For the challenge type: `image_label_area_select` (single/multi)",
    )
    SPATIAL_PATH_REASONER_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL,
        description="For the challenge type: `image_drag_drop` (single/multi)",
    )
    SUPERVISOR_MODEL: SCoTModelType = Field(
        default=DEFAULT_SCOT_MODEL,
        description="For dynamically generating reusable guidelines for solver LLMs",
    )
    SUPERVISOR_INVALIDATION_THRESHOLD: int = Field(
        default=3,
        description="Number of consecutive failures before the Supervisor guideline is regenerated",
    )
    ENABLE_SUPERVISOR: bool = Field(
        default=True,
        description="Toggle the Supervisor LLM generation on or off",
    )

    coordinate_grid: CoordinateGrid | None = Field(default_factory=CoordinateGrid)

    enable_challenger_debug: bool | None = Field(
        default=False, description="Enable debug mode"
    )

    # == Skills Configuration == #
    custom_skills_path: Path | None = Field(
        default=None, description="Path to custom skills rules.yaml"
    )
    enable_skills_update: bool = Field(
        default=False, description="Enable auto-update of skills from GitHub"
    )
    skills_update_repo: str = Field(
        default="QIN2DIM/hcaptcha-challenger",
        description="GitHub repo for skills update",
    )
    skills_update_branch: str = Field(
        default="main", description="GitHub branch for skills update"
    )

    @model_validator(mode="after")
    def validate_api_keys(self) -> "AgentConfig":
        """
        Validates that at least one API key is provided.
        """
        if not self.GEMINI_API_KEY and not self.OPENROUTER_API_KEY:
            raise ValueError(
                "Neither GEMINI_API_KEY nor OPENROUTER_API_KEY is provided. "
                "Please set at least one provider key in .env or arguments."
            )
        return self

    @property
    def active_provider(self) -> str:
        """Returns the active AI provider based on available keys."""
        if self.OPENROUTER_API_KEY:
            return "openrouter"
        return "gemini"

    @property
    def active_api_key(self) -> str:
        """Returns the active API key secret string based on active provider."""
        if self.OPENROUTER_API_KEY:
            return self.OPENROUTER_API_KEY.get_secret_value()
        return self.GEMINI_API_KEY.get_secret_value()

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
            _cache_key_temp = self.challenge_dir.joinpath(
                request_type, prompt, current_time
            )
            if self.enable_challenger_debug:
                logger.debug(
                    f"Create cache-key [NotCaptchaPayload] - {_cache_key_temp.resolve()}"
                )
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
                json.dumps(_unpacked_data, indent=2, ensure_ascii=False),
                encoding="utf8",
            )
        except Exception as e:
            logger.error(f"Failed to write captcha payload to cache: {e}")

        if self.enable_challenger_debug:
            logger.debug(f"Create cache-key [Direct] - {cache_key.resolve()}")

        return cache_key
