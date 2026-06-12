import asyncio
import math
import random
import re
from contextlib import suppress
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

import matplotlib.pyplot as plt
from loguru import logger
from playwright.async_api import Locator, expect, Page, TimeoutError, FrameLocator, Frame
from tenacity import retry, stop_after_attempt, wait_fixed

from hcaptcha_challenger.helper import create_coordinate_grid
from hcaptcha_challenger.models import RequestType, SpatialPath, CaptchaPayload
from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.skills import SkillManager
from hcaptcha_challenger.tools import (
    ImageClassifier,
    ChallengeRouter,
    SpatialPathReasoner,
    SpatialPointReasoner,
)
from hcaptcha_challenger.agent.config import AgentConfig


def _generate_bezier_trajectory(
    start: Tuple[float, float], end: Tuple[float, float], steps: int
) -> List[Tuple[float, float]]:
    """
    Generates a quadratic bezier curve trajectory between start and end points.
    """
    points = []

    # Calculate distance between points
    distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

    # Create control point(s) for the bezier curve
    # For longer distances, we use a higher control point offset
    offset_factor = min(0.3, max(0.1, distance / 1000))

    # Random control point that's offset from the midpoint
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2

    # Create slight randomness in the control point
    control_x = mid_x + random.uniform(-1, 1) * distance * offset_factor
    control_y = mid_y + random.uniform(-1, 1) * distance * offset_factor

    # Generate points along the bezier curve
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier formula
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control_x + t**2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control_y + t**2 * end[1]
        points.append((x, y))

    return points


def _generate_dynamic_delays(steps: int, base_delay: int) -> List[float]:
    """
    Generates dynamic delays between mouse movements to simulate human-like acceleration/deceleration.
    """
    delays = []

    # Acceleration profile: slower at start and end, faster in the middle
    for i in range(steps + 1):
        progress = i / steps

        # Ease in-out function (slow start, fast middle, slow end)
        if progress < 0.5:
            factor = 2 * progress * progress  # Accelerate
        else:
            progress = progress - 1
            factor = 1 - (-2 * progress * progress)  # Decelerate

        # Adjust delay based on position in the curve (1.5x at ends, 0.6x in middle)
        delay_factor = 1.5 - 0.9 * factor

        # Add slight randomness to delays (±10%)
        random_factor = random.uniform(0.9, 1.1)

        delays.append(base_delay * delay_factor * random_factor)

    return delays


class RoboticArm:
    def __init__(self, page: Page, config: AgentConfig):
        self.page = page
        self.config = config
        self._debug = config.enable_challenger_debug

        self._challenge_router = ChallengeRouter(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.CHALLENGE_CLASSIFIER_MODEL,
        )
        self._image_classifier = ImageClassifier(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.IMAGE_CLASSIFIER_MODEL,
        )
        self._spatial_path_reasoner = SpatialPathReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_PATH_REASONER_MODEL,
        )
        self._spatial_point_reasoner = SpatialPointReasoner(
            api_key=self.config.active_api_key,
            provider=self.config.active_provider,
            model=self.config.SPATIAL_POINT_REASONER_MODEL,
        )
        self._skill_manager = SkillManager(agent_config=config)
        self.signal_crumb_count: int | None = None
        self.captcha_payload: CaptchaPayload | None = None
        self._challenge_prompt: str | None = None

        self._checkbox_selector = "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=checkbox')]"
        self._challenge_selector = "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]"

    @property
    def checkbox_selector(self) -> str:
        return self._checkbox_selector

    @property
    def challenge_selector(self) -> str:
        return self._challenge_selector

    async def get_challenge_frame_locator(self) -> Frame | None:
        candidate_frame = self._find_challenge_frame_recursive(
            self.page.main_frame, max_depth=4
        )

        if candidate_frame:
            with suppress(Exception):
                challenge_view = candidate_frame.locator(
                    "//div[@class='challenge-view']"
                )
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
                and child_frame.url.startswith(
                    "https://newassets.hcaptcha.com/captcha/v1/"
                )
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

    def _match_user_prompt(self, job_type: ChallengeTypeEnum) -> str:
        try:
            challenge_prompt = (
                self.captcha_payload.get_requester_question()
                if self.captcha_payload
                else self._challenge_prompt
            )
            if challenge_prompt and isinstance(challenge_prompt, str):
                return self._skill_manager.get_skill(challenge_prompt, job_type)
        except Exception as e:
            logger.warning(f"Error while processing captcha payload: {e}")

        return f"Please note that the current task type is: {job_type.value}"

    async def click_by_mouse(self, locator: Locator):
        bbox = await locator.bounding_box()
        if bbox is None:
            raise ValueError("Element is not visible or does not exist")

        x: float = bbox["x"]
        y: float = bbox["y"]
        width: float = bbox["width"]
        height: float = bbox["height"]

        center_x = x + width / 2
        center_y = y + height / 2

        await self.page.mouse.move(center_x, center_y)

        await self.page.mouse.click(center_x, center_y, delay=150)

    async def click_checkbox(self):
        checkbox_frame = self.page.frame_locator(self.checkbox_selector)
        checkbox_element = checkbox_frame.locator("//div[@id='checkbox']")
        await self.click_by_mouse(checkbox_element)

    async def refresh_challenge(self):
        try:
            refresh_frame = await self.get_challenge_frame_locator()
            refresh_element = refresh_frame.locator("//div[@class='refresh button']")
            await self.click_by_mouse(refresh_element)
        except TimeoutError as err:
            logger.warning(f"Failed to click refresh button - {err=}")

    async def check_crumb_count(self):
        """Page turn in tasks"""
        # Determine the number of tasks based on hsw
        if isinstance(self.signal_crumb_count, int) and self.signal_crumb_count >= 1:
            return self.signal_crumb_count

        # Determine the number of tasks based on DOM
        await self.page.wait_for_timeout(500)
        frame_challenge = await self.get_challenge_frame_locator()
        crumbs = frame_challenge.locator("//div[@class='Crumb']")
        with suppress(Exception):
            crumbs_count = await crumbs.count()
            return crumbs_count if crumbs_count else 1
        return self.config.MAX_CRUMB_COUNT if await crumbs.first.is_visible() else 1

    async def check_challenge_type(self) -> RequestType | ChallengeTypeEnum | None:
        # fixme
        with suppress(Exception):
            await self.page.wait_for_selector(self.challenge_selector, timeout=1000)

        frame_challenge = await self.get_challenge_frame_locator()

        samples = frame_challenge.locator("//div[@class='task-image']")
        count = await samples.count()
        if isinstance(count, int) and count == 9:
            return RequestType.IMAGE_LABEL_BINARY
        if isinstance(count, int) and count == 0:
            tms = self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS * 1.5
            await self.page.wait_for_timeout(tms)
            challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
            cache_path = self.config.cache_dir.joinpath(
                f"challenge_view/_artifacts/{uuid4()}.png"
            )
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            await challenge_view.screenshot(type="png", path=cache_path)
            router_result = await self._challenge_router(
                challenge_screenshot=cache_path
            )
            self._challenge_prompt = router_result.challenge_prompt
            return router_result.challenge_type
        return None

    async def _wait_for_all_loaders_complete(self):
        """Wait for all loading indicators to complete (become invisible)"""
        frame_challenge = await self.get_challenge_frame_locator()

        await self.page.wait_for_timeout(
            self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS
        )

        loading_indicators = frame_challenge.locator(
            "//div[@class='loading-indicator']"
        )
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
                await loading_indicators.nth(i).get_attribute(
                    "style"
                )  # It cannot be removed
            except TimeoutError:
                logger.warning(
                    f"The load indicator {i + 1}/{count} waits for a timeout"
                )
            except ValueError:
                # todo requires smarter waiting methods
                await self.page.wait_for_timeout(130)

        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry request ({retry_state.attempt_number}/2) - Wait 1 second - Exception: {retry_state.outcome.exception()}"
        ),
    )
    async def _capture_spatial_mapping(
        self,
        frame_challenge: FrameLocator | Frame,
        cache_key: Path,
        crumb_id: int | str,
    ):
        # Capture challenge-view
        challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
        challenge_screenshot = cache_key.joinpath(
            f"{cache_key.name}_{crumb_id}_challenge_view.png"
        )
        challenge_screenshot.parent.mkdir(parents=True, exist_ok=True)
        await challenge_view.screenshot(type="png", path=challenge_screenshot)

        challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
        bbox = await challenge_view.bounding_box()

        # Save grid field
        result = create_coordinate_grid(
            challenge_screenshot,
            bbox,
            x_line_space_num=self.config.coordinate_grid.x_line_space_num,
            y_line_space_num=self.config.coordinate_grid.y_line_space_num,
            color=self.config.coordinate_grid.color,
            adaptive_contrast=self.config.coordinate_grid.adaptive_contrast,
        )

        grid_divisions = cache_key.joinpath(
            f"{cache_key.name}_{crumb_id}_spatial_helper.png"
        )
        grid_divisions.parent.mkdir(parents=True, exist_ok=True)
        plt.imsave(str(grid_divisions.resolve()), result)

        return challenge_screenshot, grid_divisions

    async def _perform_drag_drop(
        self, path: SpatialPath, steps: int = 25, delay_ms: int = 15
    ):
        """
        Performs a human-like drag and drop operation using bezier curve trajectory.

        Args:
            path: The SpatialPath containing start and end coordinates
            steps: Number of intermediate steps for the mouse movement
            delay_ms: Base delay between steps in milliseconds
        """
        start_x, start_y = path.start_point.x, path.start_point.y
        end_x, end_y = path.end_point.x, path.end_point.y

        if self.config.DISABLE_BEZIER_TRAJECTORY:
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            await self.page.mouse.move(end_x, end_y)
            await self.page.mouse.up()
            return

        # Move to the starting position
        await self.page.mouse.move(start_x, start_y)

        # Small random delay before pressing down (human reaction time)
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # Press the mouse button down
        await self.page.mouse.down()

        # Generate a bezier curve path with a control point
        points = _generate_bezier_trajectory((start_x, start_y), (end_x, end_y), steps)

        # Add velocity variation (slow start, fast middle, slow end)
        delays = _generate_dynamic_delays(steps, base_delay=delay_ms)

        # Perform the drag with human-like movement
        for i, ((current_x, current_y), delay) in enumerate(zip(points, delays)):
            # Add slight "noise" to the path (more pronounced near the end)
            if i > steps * 0.7:  # In the last 30% of the movement
                # More micro-adjustments near the end
                noise_factor = 0.5 if i > steps * 0.9 else 0.2
                current_x += random.uniform(-noise_factor, noise_factor)
                current_y += random.uniform(-noise_factor, noise_factor)

            await self.page.mouse.move(current_x, current_y)
            await asyncio.sleep(delay / 1000)

        # Ensure we end exactly at the target position
        await self.page.mouse.move(end_x, end_y)

        # Small pause before releasing (human precision adjustment)
        await asyncio.sleep(random.uniform(0.05, 0.1))

        # Release the mouse button at the destination
        await self.page.mouse.up()

        # Small pause between drag operations
        await asyncio.sleep(random.uniform(0.08, 0.12))

    async def challenge_image_label_binary(self):
        frame_challenge = await self.get_challenge_frame_locator()
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)

        for cid in range(crumb_count):
            await self._wait_for_all_loaders_complete()

            # Get challenge-view
            challenge_view = frame_challenge.locator("//div[@class='challenge-view']")
            challenge_screenshot = cache_key.joinpath(
                f"{cache_key.name}_{cid}_challenge_view.png"
            )
            await challenge_view.screenshot(type="png", path=challenge_screenshot)

            # Image classification
            response = await self._image_classifier(
                challenge_screenshot=challenge_screenshot
            )
            boolean_matrix = response.convert_box_to_boolean_matrix()

            logger.debug(
                f"[{cid + 1}/{crumb_count}]ToolInvokeMessage: {response.log_message}"
            )
            self._image_classifier.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            # drive the browser to work on the challenge
            positive_cases = 0
            xpath_task_image = (
                "//div[@class='task' and contains(@aria-label, '{index}')]"
            )
            for i, should_be_clicked in enumerate(boolean_matrix):
                if should_be_clicked:
                    task_image = frame_challenge.locator(
                        xpath_task_image.format(index=i + 1)
                    )
                    await self.click_by_mouse(task_image)
                    positive_cases += 1
                elif positive_cases == 0 and i == len(boolean_matrix) - 1:
                    task_image = frame_challenge.locator(
                        xpath_task_image.format(index=1)
                    )
                    await self.click_by_mouse(task_image)

            # {{< Verify >}}
            with suppress(TimeoutError):
                submit_btn = frame_challenge.locator(
                    "//div[@class='button-submit button']"
                )
                await self.click_by_mouse(submit_btn)

    async def challenge_image_drag_drop(self, job_type: ChallengeTypeEnum):
        frame_challenge = await self.get_challenge_frame_locator()
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)

        for cid in range(crumb_count):
            await self.page.wait_for_timeout(
                self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS
            )

            raw, projection = await self._capture_spatial_mapping(
                frame_challenge, cache_key, cid
            )

            user_prompt = self._match_user_prompt(job_type)

            response = await self._spatial_path_reasoner(
                challenge_screenshot=raw,
                grid_divisions=projection,
                auxiliary_information=user_prompt,
            )
            logger.debug(
                f"[{cid + 1}/{crumb_count}]ToolInvokeMessage: {response.log_message}"
            )
            self._spatial_path_reasoner.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            for path in response.paths:
                await self._perform_drag_drop(path)

            # {{< Verify >}}
            with suppress(TimeoutError):
                submit_btn = frame_challenge.locator(
                    "//div[@class='button-submit button']"
                )
                await self.click_by_mouse(submit_btn)

    async def challenge_image_label_select(self, job_type: ChallengeTypeEnum):
        frame_challenge = await self.get_challenge_frame_locator()
        crumb_count = await self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)

        for cid in range(crumb_count):
            await self.page.wait_for_timeout(
                self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS
            )

            raw, projection = await self._capture_spatial_mapping(
                frame_challenge, cache_key, cid
            )

            user_prompt = self._match_user_prompt(job_type)

            response = await self._spatial_point_reasoner(
                challenge_screenshot=raw,
                grid_divisions=projection,
                auxiliary_information=user_prompt,
            )
            logger.debug(
                f"[{cid + 1}/{crumb_count}]ToolInvokeMessage: {response.log_message}"
            )
            self._spatial_point_reasoner.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            for point in response.points:
                await self.page.mouse.click(point.x, point.y, delay=180)
                await self.page.wait_for_timeout(500)

            # {{< Verify >}}
            with suppress(TimeoutError):
                submit_btn = frame_challenge.locator(
                    "//div[@class='button-submit button']"
                )
                await self.click_by_mouse(submit_btn)
