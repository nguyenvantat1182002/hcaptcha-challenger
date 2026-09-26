from playwright.async_api import Frame, Locator, Page

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.driver import BrowserArm
from hcaptcha_challenger.agent.pointer import HumanoidPointer
from hcaptcha_challenger.agent.solvers import ChallengeContext, SolverRegistry
from hcaptcha_challenger.models import CaptchaPayload, ChallengeTypeEnum, RequestType


class RoboticArm:
    """
    Backward-compatible facade wrapping BrowserArm, HumanoidPointer, and Solvers.
    """

    def __init__(
        self,
        page: Page,
        config: AgentConfig,
        arm: BrowserArm | None = None,
        pointer: HumanoidPointer | None = None,
        registry: SolverRegistry | None = None,
    ):
        self.page = page
        self.config = config
        self.pointer = pointer or HumanoidPointer(
            page=page, disable_bezier_trajectory=config.DISABLE_BEZIER_TRAJECTORY
        )
        self.arm = arm or BrowserArm(page=page, config=config, pointer=self.pointer)
        self.registry = registry
        self.signal_crumb_count: int | None = None
        self.captcha_payload: CaptchaPayload | None = None

    @property
    def checkbox_selector(self) -> str:
        return self.arm.checkbox_selector

    @property
    def challenge_selector(self) -> str:
        return self.arm.challenge_selector

    async def get_challenge_frame_locator(self) -> Frame | None:
        return await self.arm.get_challenge_frame_locator()

    async def click_by_mouse(self, locator: Locator):
        await self.pointer.click(locator)

    async def click_checkbox(self):
        await self.arm.click_checkbox()

    async def refresh_challenge(self):
        await self.arm.refresh_challenge()

    async def check_crumb_count(self) -> int:
        if isinstance(self.signal_crumb_count, int) and self.signal_crumb_count >= 1:
            return self.signal_crumb_count
        return await self.arm.check_crumb_count()

    async def check_challenge_type(self) -> RequestType | ChallengeTypeEnum | None:
        return await self.arm.check_challenge_type()

    async def challenge_image_label_binary(self):
        frame = await self.get_challenge_frame_locator()
        if not frame:
            return None
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)
        ctx = ChallengeContext(
            frame=frame,
            crumb_count=crumb_count,
            cache_key=cache_key,
            payload=self.captcha_payload,
            job_type=RequestType.IMAGE_LABEL_BINARY,
        )
        solver = self.registry.get(RequestType.IMAGE_LABEL_BINARY) if self.registry else None
        if solver:
            return await solver.solve(ctx)

    async def challenge_image_drag_drop(self, job_type: ChallengeTypeEnum):
        frame = await self.get_challenge_frame_locator()
        if not frame:
            return None
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)
        ctx = ChallengeContext(
            frame=frame,
            crumb_count=crumb_count,
            cache_key=cache_key,
            payload=self.captcha_payload,
            job_type=job_type,
        )
        solver = self.registry.get(job_type) if self.registry else None
        if solver:
            return await solver.solve(ctx)

    async def challenge_image_label_select(self, job_type: ChallengeTypeEnum):
        frame = await self.get_challenge_frame_locator()
        if not frame:
            return None
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)
        ctx = ChallengeContext(
            frame=frame,
            crumb_count=crumb_count,
            cache_key=cache_key,
            payload=self.captcha_payload,
            job_type=job_type,
        )
        solver = self.registry.get(job_type) if self.registry else None
        if solver:
            return await solver.solve(ctx)
