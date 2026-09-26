from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import Frame

from hcaptcha_challenger.models import CaptchaPayload, ChallengeTypeEnum, RequestType


@dataclass(frozen=True)
class ChallengeContext:
    """
    Immutable execution state passed across the solver seam.
    """

    frame: Frame
    crumb_count: int
    cache_key: Path
    payload: CaptchaPayload | None
    job_type: ChallengeTypeEnum | RequestType


class ChallengeSolver(ABC):
    """
    Abstract interface for specialized challenge solver modules.
    """

    @abstractmethod
    async def solve(self, ctx: ChallengeContext) -> None:
        """
        Executes end-to-end challenge resolution for this challenge type.
        """
