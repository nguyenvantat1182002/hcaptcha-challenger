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

    async def report_feedback(self, is_correct: bool = False) -> None:
        """
        Reports accuracy feedback for tasks executed by this solver.
        Default implementation delegates to YesCaptchaClient if available.
        """
        client = getattr(self, "_yescaptcha_client", None)
        if client is not None:
            await client.report_recent_tasks(is_correct=is_correct)

    def clear_feedback(self) -> None:
        """
        Clears pending feedback tasks when challenge succeeds.
        """
        client = getattr(self, "_yescaptcha_client", None)
        if client is not None:
            client.clear_recent_tasks()
