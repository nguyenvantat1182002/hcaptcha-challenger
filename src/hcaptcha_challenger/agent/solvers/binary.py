from contextlib import suppress

from loguru import logger
from playwright.async_api import TimeoutError

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.driver import BrowserArm
from hcaptcha_challenger.agent.pointer import HumanoidPointer
from hcaptcha_challenger.agent.solvers.base import ChallengeContext, ChallengeSolver
from hcaptcha_challenger.tools import ImageClassifier


class BinaryLabelSolver(ChallengeSolver):
    """
    Solves 9-image binary label challenges (IMAGE_LABEL_BINARY).
    """

    def __init__(
        self,
        config: AgentConfig,
        driver: BrowserArm,
        pointer: HumanoidPointer,
    ):
        self.config = config
        self.driver = driver
        self.pointer = pointer

        self._image_classifier = ImageClassifier(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.IMAGE_CLASSIFIER_MODEL,
        )

    async def solve(self, ctx: ChallengeContext) -> None:
        for cid in range(ctx.crumb_count):
            await self.driver.wait_for_all_loaders_complete()

            # Screenshot challenge view
            challenge_view = ctx.frame.locator("//div[@class='challenge-view']")
            challenge_screenshot = ctx.cache_key.joinpath(
                f"{ctx.cache_key.name}_{cid}_challenge_view.png"
            )
            await challenge_view.screenshot(type="png", path=challenge_screenshot)

            # Image classification
            response = await self._image_classifier(challenge_screenshot=challenge_screenshot)
            boolean_matrix = response.convert_box_to_boolean_matrix()

            logger.debug(f"[{cid + 1}/{ctx.crumb_count}]ToolInvokeMessage: {response.log_message}")
            self._image_classifier.cache_response(
                path=ctx.cache_key.joinpath(f"{ctx.cache_key.name}_{cid}_model_answer.json")
            )

            # Click tasks in DOM
            positive_cases = 0
            xpath_task_image = "//div[@class='task' and contains(@aria-label, '{index}')]"
            for i, should_be_clicked in enumerate(boolean_matrix):
                if should_be_clicked:
                    task_image = ctx.frame.locator(xpath_task_image.format(index=i + 1))
                    await self.pointer.click(task_image)
                    positive_cases += 1
                elif positive_cases == 0 and i == len(boolean_matrix) - 1:
                    task_image = ctx.frame.locator(xpath_task_image.format(index=1))
                    await self.pointer.click(task_image)

            # Verify / Submit
            with suppress(TimeoutError):
                submit_btn = ctx.frame.locator("//div[@class='button-submit button']")
                await self.pointer.click(submit_btn)
