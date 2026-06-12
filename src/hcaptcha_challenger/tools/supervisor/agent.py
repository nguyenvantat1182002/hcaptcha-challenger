from pathlib import Path
from typing import Union

from pydantic import BaseModel, Field

from hcaptcha_challenger.models import SCoTModelType
from hcaptcha_challenger.tools.internal.base import Reasoner
from hcaptcha_challenger.utils import load_desc


class SupervisorResponse(BaseModel):
    guideline: str = Field(description="The general strategy guideline string.")


class SupervisorReasoner(Reasoner[SCoTModelType, SupervisorResponse]):
    """
    Supervisor AI tool for generating dynamic instructions.
    """

    description: str = load_desc(Path(__file__).parent / "supervisor.md")

    async def __call__(
        self,
        *,
        challenge_prompt: str,
        challenge_screenshot: Union[str, Path],
        **kwargs,
    ) -> str:
        """
        Analyze the challenge and return the strategy string.

        Args:
            challenge_prompt: The prompt given to the solver (e.g. "Find the horse")
            challenge_screenshot: Path to the sample challenge image.
            **kwargs: Additional provider options.

        Returns:
            The generated guideline string.
        """
        response = await self._provider.generate_with_images(
            images=[Path(challenge_screenshot)],
            user_prompt=challenge_prompt,
            description=self.description,
            response_schema=SupervisorResponse,
            **kwargs,
        )
        return response.guideline
