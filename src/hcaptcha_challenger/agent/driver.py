import re
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

import matplotlib.pyplot as plt
from loguru import logger
from playwright.async_api import (
    Frame,
    FrameLocator,
    Locator,
    Page,
    TimeoutError,
    expect,
)
from tenacity import retry, stop_after_attempt, wait_fixed

from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.pointer import HumanoidPointer
from hcaptcha_challenger.helper import create_coordinate_grid
from hcaptcha_challenger.models import ChallengeImage, ChallengeTypeEnum, RequestType
from hcaptcha_challenger.tools import ChallengeRouter


class BrowserArm:
    """
    Manages low-level browser automation: frame locator resolution, element clicks,
    challenge reloading, loader indicator waiting, and fallback visual routing.
    """

    def __init__(
        self, page: Page, config: AgentConfig, pointer: HumanoidPointer | None = None
    ):
        self.page = page
        self.config = config
        self.pointer = pointer or HumanoidPointer(
            page=page, disable_bezier_trajectory=config.DISABLE_BEZIER_TRAJECTORY
        )
        self._debug = config.enable_challenger_debug

        self._challenge_router = ChallengeRouter(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.CHALLENGE_CLASSIFIER_MODEL,
        )
        self.signal_crumb_count: int | None = None
        self._challenge_prompt: str | None = None

        self._checkbox_selector = (
            "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') "
            "and contains(@src, 'frame=checkbox')]"
        )
        self._challenge_selector = (
            "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') "
            "and contains(@src, 'frame=challenge')]"
        )

    @property
    def checkbox_selector(self) -> str:
        return self._checkbox_selector

    @property
    def challenge_selector(self) -> str:
        return self._challenge_selector

    @property
    def challenge_prompt(self) -> str | None:
        return self._challenge_prompt

    async def get_challenge_frame_locator(self) -> Frame | None:
        candidate_frame = self._find_challenge_frame_recursive(self.page.main_frame, max_depth=4)

        if candidate_frame:
            with suppress(Exception):
                challenge_view = candidate_frame.locator("//div[@class='challenge-view']")
                is_visible = await challenge_view.is_visible(timeout=1000)
                if is_visible:
                    return candidate_frame

        try:
            challenge_frames = []
            all_frames = self.page.frames
            for frame in all_frames:
                if (
                    frame.url.startswith("https://newassets.hcaptcha.com/captcha/v1/")
                    and "frame=challenge" in frame.url
                ):
                    challenge_frames.append(frame)

            for frame in challenge_frames:
                with suppress(Exception):
                    challenge_view = frame.locator("//div[@class='challenge-view']")
                    if await challenge_view.is_visible():
                        return frame
        except Exception as e:
            logger.error(f"Error finding all iframes: {e}")

        logger.error("Cannot find a valid challenge frame")
        return None

    def _find_challenge_frame_recursive(
        self, frame: Frame, current_depth=0, max_depth=4
    ) -> Frame | None:
        if current_depth >= max_depth:
            return None

        candidate_frames = []

        for child_frame in frame.child_frames:
            if (
                not child_frame.child_frames
                and child_frame.url.startswith("https://newassets.hcaptcha.com/captcha/v1/")
                and "frame=challenge" in child_frame.url
            ):
                candidate_frames.append(child_frame)
            else:
                found_in_child = self._find_challenge_frame_recursive(
                    child_frame, current_depth + 1, max_depth
                )
                if found_in_child:
                    return found_in_child

        if candidate_frames:
            return candidate_frames[0]

        return None

    async def click_by_mouse(self, locator: Locator):
        await self.pointer.click(locator)

    async def click_checkbox(self):
        checkbox_frame = self.page.frame_locator(self.checkbox_selector)
        checkbox_element = checkbox_frame.locator("//div[@id='checkbox']")
        await self.pointer.click(checkbox_element)

    async def refresh_challenge(self):
        try:
            refresh_frame = await self.get_challenge_frame_locator()
            if refresh_frame:
                refresh_element = refresh_frame.locator("//div[@class='refresh button']")
                await self.pointer.click(refresh_element)
        except TimeoutError as err:
            logger.warning(f"Failed to click refresh button - {err=}")

    async def check_crumb_count(self) -> int:
        """Page turn in tasks"""
        if isinstance(self.signal_crumb_count, int) and self.signal_crumb_count >= 1:
            return self.signal_crumb_count

        await self.page.wait_for_timeout(500)
        frame_challenge = await self.get_challenge_frame_locator()
        if not frame_challenge:
            return 1

        crumbs = frame_challenge.locator("//div[@class='Crumb']")
        with suppress(Exception):
            crumbs_count = await crumbs.count()
            return crumbs_count if crumbs_count else 1
        return self.config.MAX_CRUMB_COUNT if await crumbs.first.is_visible() else 1

    async def check_challenge_type(self) -> RequestType | ChallengeTypeEnum | None:
        with suppress(Exception):
            await self.page.wait_for_selector(self.challenge_selector, timeout=1000)

        frame_challenge = await self.get_challenge_frame_locator()
        if not frame_challenge:
            return None

        samples = frame_challenge.locator("//div[@class='task-image']")
        count = await samples.count()
        if isinstance(count, int) and count == 9:
            return RequestType.IMAGE_LABEL_BINARY
        if isinstance(count, int) and count == 0:
            tms = self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS * 1.5
            await self.page.wait_for_timeout(tms)
            challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
            cache_path = self.config.cache_dir.joinpath(f"challenge_view/_artifacts/{uuid4()}.png")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            await challenge_view.screenshot(type="png", path=cache_path)
            router_result = await self._challenge_router(challenge_screenshot=cache_path)
            self._challenge_prompt = router_result.challenge_prompt
            return router_result.challenge_type
        return None

    async def wait_for_all_loaders_complete(self):
        """Wait for all loading indicators to complete (become invisible)"""
        frame_challenge = await self.get_challenge_frame_locator()
        if not frame_challenge:
            return True

        await self.page.wait_for_timeout(self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS)

        loading_indicators = frame_challenge.locator("//div[@class='loading-indicator']")
        count = await loading_indicators.count()

        if count == 0:
            logger.info("No load indicator found in the page")
            return True

        for i in range(count):
            loader = loading_indicators.nth(i)
            try:
                await expect(loader).to_have_attribute(
                    "style", re.compile(r"opacity:\s*0"), timeout=30000
                )
                await loading_indicators.nth(i).get_attribute("style")
            except TimeoutError:
                logger.warning(f"The load indicator {i + 1}/{count} waits for a timeout")
            except ValueError:
                await self.page.wait_for_timeout(130)

        return True

    # Alias for backward compatibility
    _wait_for_all_loaders_complete = wait_for_all_loaders_complete

    async def capture_challenge_image(
        self, frame_challenge: FrameLocator | Frame
    ) -> tuple[ChallengeImage, dict | None]:
        """
        Capture challenge screenshot directly in-memory as ChallengeImage alongside its bounding box.
        Operates with zero disk I/O.
        """
        challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
        png_bytes = await challenge_view.screenshot(type="png")
        bbox = await challenge_view.bounding_box()
        return ChallengeImage.from_bytes(png_bytes), bbox

    def create_spatial_projection(
        self,
        challenge_image: ChallengeImage | str | Path,
        bbox: dict | None,
        cache_key: Path,
        crumb_id: int | str = 0,
    ) -> Path:
        """
        Render coordinate grid projection overlay for visual reasoning (Gemini).
        """
        if bbox is None:
            raise ValueError("Bounding box is required to create coordinate grid projection.")

        if isinstance(challenge_image, ChallengeImage):
            temp_path = cache_key.joinpath(f"{cache_key.name}_{crumb_id}_challenge_view.png")
            challenge_image.save(temp_path)
            img_input = temp_path
        else:
            img_input = Path(challenge_image)

        result = create_coordinate_grid(
            img_input,
            bbox,
            x_line_space_num=self.config.coordinate_grid.x_line_space_num,
            y_line_space_num=self.config.coordinate_grid.y_line_space_num,
            color=self.config.coordinate_grid.color,
            adaptive_contrast=self.config.coordinate_grid.adaptive_contrast,
        )

        grid_divisions = cache_key.joinpath(f"{cache_key.name}_{crumb_id}_spatial_helper.png")
        grid_divisions.parent.mkdir(parents=True, exist_ok=True)
        plt.imsave(str(grid_divisions.resolve()), result)
        return grid_divisions

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry request ({retry_state.attempt_number}/2) - Wait 1 second - Exception: {retry_state.outcome.exception()}"
        ),
    )
    async def capture_spatial_mapping(
        self, frame_challenge: FrameLocator | Frame, cache_key: Path, crumb_id: int | str
    ):
        challenge_image, bbox = await self.capture_challenge_image(frame_challenge)
        challenge_screenshot = cache_key.joinpath(f"{cache_key.name}_{crumb_id}_challenge_view.png")
        challenge_image.save(challenge_screenshot)

        grid_divisions = self.create_spatial_projection(
            challenge_image=challenge_image,
            bbox=bbox,
            cache_key=cache_key,
            crumb_id=crumb_id,
        )
        return challenge_screenshot, grid_divisions

    # Alias for backward compatibility
    _capture_spatial_mapping = capture_spatial_mapping

