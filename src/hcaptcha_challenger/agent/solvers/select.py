from contextlib import suppress

from loguru import logger
from playwright.async_api import TimeoutError

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.driver import BrowserArm
from hcaptcha_challenger.agent.pointer import HumanoidPointer
from hcaptcha_challenger.agent.solvers.base import ChallengeContext, ChallengeSolver
from hcaptcha_challenger.models import CaptchaPayload, ChallengeTypeEnum, RequestType
from hcaptcha_challenger.skills import SkillManager
from hcaptcha_challenger.tools import SpatialPointReasoner
from hcaptcha_challenger.tools.yescaptcha import (
    YesCaptchaClient,
    YesCaptchaPointReasoner,
)


class AreaSelectSolver(ChallengeSolver):
    """
    Solves area selection challenges (IMAGE_LABEL_SINGLE_SELECT, IMAGE_LABEL_MULTI_SELECT).
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

        if self.config.REASONING_PROVIDER == "yescaptcha":
            client = YesCaptchaClient(
                client_key=self.config.YESCAPTCHA_CLIENT_KEY,
                dump_dir=self.config.YESCAPTCHA_DUMP_DIR,
            )
            self._spatial_point_reasoner = YesCaptchaPointReasoner(client=client)
        else:
            self._spatial_point_reasoner = SpatialPointReasoner(
                gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
                model=self.config.SPATIAL_POINT_REASONER_MODEL,
            )
        self._skill_manager = SkillManager(agent_config=config)

    def _match_user_prompt(
        self,
        payload: CaptchaPayload | None,
        job_type: ChallengeTypeEnum | RequestType,
    ) -> str:
        try:
            challenge_prompt = (
                payload.get_requester_question()
                if payload
                else self.driver.challenge_prompt
            )
            if challenge_prompt and isinstance(challenge_prompt, str):
                return self._skill_manager.get_skill(challenge_prompt, job_type)
        except Exception as e:
            logger.warning(f"Error while processing captcha payload: {e}")

        job_val = getattr(job_type, "value", str(job_type))
        return f"Please note that the current task type is: {job_val}"

    async def solve(self, ctx: ChallengeContext) -> None:
        for cid in range(ctx.crumb_count):
            await self.driver.page.wait_for_timeout(
                self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS
            )

            # Capture challenge image directly in-memory alongside bounding box
            challenge_image, bbox = await self.driver.capture_challenge_image(ctx.frame)

            # Generate coordinate grid projection only if active reasoner requires it (Gemini)
            projection = None
            if getattr(self._spatial_point_reasoner, "requires_grid_projection", False):
                projection = self.driver.create_spatial_projection(
                    challenge_image=challenge_image,
                    bbox=bbox,
                    cache_key=ctx.cache_key,
                    crumb_id=cid,
                )

            # Save diagnostic screenshot only when debug mode is explicitly enabled
            if self.config.enable_challenger_debug:
                raw_path = ctx.cache_key.joinpath(f"{ctx.cache_key.name}_{cid}_challenge_view.png")
                challenge_image.save(raw_path)

            user_prompt = self._match_user_prompt(ctx.payload, ctx.job_type)

            response = await self._spatial_point_reasoner(
                challenge_screenshot=challenge_image,
                grid_divisions=projection,
                auxiliary_information=user_prompt,
                payload=ctx.payload,
                bbox=bbox,
            )
            logger.debug(f"[{cid + 1}/{ctx.crumb_count}]ToolInvokeMessage: {response.log_message}")

            if self.config.enable_challenger_debug:
                self._spatial_point_reasoner.cache_response(
                    path=ctx.cache_key.joinpath(f"{ctx.cache_key.name}_{cid}_model_answer.json")
                )

            for point in response.points:
                await self.pointer.click_at(point.x, point.y, delay=180)
                await self.driver.page.wait_for_timeout(500)

            # Verify / Submit
            with suppress(TimeoutError):
                submit_btn = ctx.frame.locator("//div[@class='button-submit button']")
                await self.pointer.click(submit_btn)
