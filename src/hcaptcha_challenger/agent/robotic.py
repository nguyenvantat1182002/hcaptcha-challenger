import base64
import matplotlib.pyplot as plt
import re

from typing import Tuple
from pathlib import Path
from uuid import uuid4
from loguru import logger
from DrissionPage._pages.chromium_frame import ChromiumFrame
from DrissionPage._elements.chromium_element import ChromiumElement
from DrissionPage.common import wait_until
from tenacity import retry, stop_after_attempt, wait_fixed
from contextlib import suppress

from hcaptcha_challenger.agent.mouse import (
    human_move, human_click, click_target
)
from hcaptcha_challenger.agent.mouse_config import (
    resolve_config, sleep_ms, rand
)


from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.helper import create_coordinate_grid
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.skills import SkillManager
from hcaptcha_challenger.tools import (
    ImageClassifier,
    ChallengeRouter,
    SpatialPathReasoner,
    SpatialPointReasoner,
)
from hcaptcha_challenger.models import (
    RequestType,
    SpatialPath,
    CaptchaPayload,
)


class DrissionPageMouse:
    """Adapter bridging mouse.py's RawMouse protocol to DrissionPage Actions.

    Wraps ``frame.tab.actions`` (the top-level tab's Actions instance),
    translating iframe-local coordinates to absolute page viewport coordinates.
    Single-point moves are dispatched directly because ``human_move()``
    already handles trajectory; we skip Actions' built-in linear interpolation.
    """

    def __init__(self, frame: ChromiumFrame):
        self._frame = frame
        self._actions = frame.tab.actions
        self.curr_x: float = 0
        self.curr_y: float = 0

    def _frame_offset(self) -> Tuple[float, float]:
        """Iframe top-left on page viewport, including border."""
        fx, fy = self._frame.frame_ele.rect.viewport_location
        try:
            bt = float(self._frame.frame_ele.style('border-top-width').replace('px', ''))
            bl = float(self._frame.frame_ele.style('border-left-width').replace('px', ''))
        except (ValueError, AttributeError):
            bt, bl = 0, 0
        return fx + bl, fy + bt

    def _sync_actions_pos(self) -> None:
        """Keep actions' internal cursor in sync with ours."""
        ox, oy = self._frame_offset()
        self._actions.curr_x = ox + self.curr_x
        self._actions.curr_y = oy + self.curr_y

    def move(self, x: float, y: float) -> None:
        self.curr_x = x
        self.curr_y = y
        self._sync_actions_pos()
        # Single-point move — bypass actions.move() linear interpolation
        self._actions._dr.run(
            'Input.dispatchMouseEvent',
            type='mouseMoved', button=self._actions._holding,
            x=self._actions.curr_x, y=self._actions.curr_y,
            modifiers=self._actions.modifier,
        )

    def down(self) -> None:
        self._sync_actions_pos()
        self._actions._hold()

    def up(self) -> None:
        self._sync_actions_pos()
        self._actions._release('left')

    def wheel(self, delta_x: float, delta_y: float) -> None:
        self._sync_actions_pos()
        self._actions.scroll(delta_y=delta_y, delta_x=delta_x)


class RoboticArm:
    def __init__(self, page: ChromiumFrame, config: AgentConfig):
        self.page = page
        self.config = config
        self._debug = config.enable_challenger_debug

        # Human-like mouse adapter
        self._human_cfg = resolve_config("default", overrides={"mouse_speed": config.MOUSE_SPEED})
        self._raw_mouse = DrissionPageMouse(page)

        self._challenge_router = ChallengeRouter(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.CHALLENGE_CLASSIFIER_MODEL,
        )
        self._image_classifier = ImageClassifier(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.IMAGE_CLASSIFIER_MODEL,
        )
        self._spatial_path_reasoner = SpatialPathReasoner(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.SPATIAL_PATH_REASONER_MODEL,
        )
        self._spatial_point_reasoner = SpatialPointReasoner(
            gemini_api_key=self.config.GEMINI_API_KEY.get_secret_value(),
            model=self.config.SPATIAL_POINT_REASONER_MODEL,
        )
        self._skill_manager = SkillManager(agent_config=config)
        self.signal_crumb_count: int | None = None
        self.captcha_payload: CaptchaPayload | None = None
        self._challenge_prompt: str | None = None

        self._checkbox_selector = "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=checkbox')]"
        self._challenge_selector = "//iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]"

    def screenshot_element_in_frame(self, element: ChromiumElement, save_path: Path) -> Path:
        """Capture a screenshot of an element inside an iframe using CDP directly.

        DrissionPage's built-in element.get_screenshot() has a coordinate mapping
        bug for elements inside iframes. CDP's Page.captureScreenshot only works
        on top-level targets.

        This method:
        1. Gets element rect via JS getBoundingClientRect() (iframe-relative)
        2. Gets iframe position on page via frame_ele.rect.viewport_location
        3. Adds iframe border offsets for accurate absolute coordinates
        4. Captures from top-level tab with clip at the computed absolute position
        """
        # Scroll element into view within the iframe
        element._run_js('this.scrollIntoView({block: "center"});')

        # Get element's bounding rect relative to iframe viewport
        rect = element._run_js('return this.getBoundingClientRect().toJSON();')

        # Get iframe element's position on the top-level page viewport
        frame_left, frame_top = self.page.frame_ele.rect.viewport_location

        # Account for iframe border width
        try:
            bt = float(self.page.frame_ele.style('border-top-width').replace('px', ''))
            bl = float(self.page.frame_ele.style('border-left-width').replace('px', ''))
        except (ValueError, AttributeError):
            bt, bl = 0, 0

        # Get device pixel ratio
        dpr = self.page._run_js('return window.devicePixelRatio;')

        # Compute absolute position and size
        # If multiplication (* dpr) moved content to bottom-right (meaning clip origin was too small),
        # we try division (/ dpr) to shift the clip origin further and capture the correct area.
        if dpr != 1.0:
            scale_factor = 1 / dpr
            lx = (frame_left + bl + rect['x']) * scale_factor
            ly = (frame_top + bt + rect['y']) * scale_factor
            lw = rect['width'] * scale_factor
            lh = rect['height'] * scale_factor
        else:
            lx = frame_left + bl + rect['x']
            ly = frame_top + bt + rect['y']
            lw = rect['width']
            lh = rect['height']

        # Capture from top-level tab
        data = self.page.tab._run_cdp(
            'Page.captureScreenshot',
            format='png',
            clip={
                'x': lx,
                'y': ly,
                'width': lw,
                'height': lh,
                'scale': 1
            }
        )
        img_bytes = base64.b64decode(data['data'])

        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(img_bytes)
        return save_path


    @property
    def checkbox_selector(self) -> str:
        return self._checkbox_selector

    @property
    def challenge_selector(self) -> str:
        return self._challenge_selector

    def get_challenge_frame_locator(self) -> ChromiumFrame:
        return self.page
        
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

    def click_element(self, element: ChromiumElement, is_input: bool = False):
        """Human-like click on a DrissionPage element using bezier mouse movement."""
        rect = element._run_js('return this.getBoundingClientRect().toJSON();')
        target = click_target(rect, is_input, self._human_cfg)

        human_move(
            self._raw_mouse,
            self._raw_mouse.curr_x, self._raw_mouse.curr_y,
            target.x, target.y,
            self._human_cfg,
        )
        human_click(self._raw_mouse, is_input, self._human_cfg)

    def click_at(self, x: float, y: float):
        """Human-like click at absolute iframe-local coordinates."""
        human_move(
            self._raw_mouse,
            self._raw_mouse.curr_x, self._raw_mouse.curr_y,
            x, y,
            self._human_cfg,
        )
        human_click(self._raw_mouse, is_input=False, cfg=self._human_cfg)

    def click_checkbox(self):
        """Click the hCaptcha checkbox in the parent page."""
        checkbox_frame = self.page.parent().ele(self.checkbox_selector)
        if checkbox_frame:
            checkbox_ele = checkbox_frame.ele("css:div[id='checkbox']")
            self.click_element(checkbox_ele)
            
    def check_crumb_count(self) -> int:
        """Page turn in tasks"""
        # # Determine the number of tasks based on hsw
        # if isinstance(self.signal_crumb_count, int) and self.signal_crumb_count >= 1:
        #     return self.signal_crumb_count

        # # Determine the number of tasks based on DOM
        # await self.page.wait_for_timeout(500)
        # frame_challenge = await self.get_challenge_frame_locator()
        # crumbs = frame_challenge.locator("//div[@class='Crumb']")
        # with suppress(Exception):
        #     crumbs_count = await crumbs.count()
        #     return crumbs_count if crumbs_count else 1
        # return self.config.MAX_CRUMB_COUNT if await crumbs.first.is_visible() else 1

        return self.signal_crumb_count

    def check_challenge_type(self) -> RequestType | ChallengeTypeEnum | None:
        samples = self.page.eles("css:div[class='task-image']")
        count = len(samples)

        if isinstance(count, int) and count == 9:
            return RequestType.IMAGE_LABEL_BINARY
            
        if isinstance(count, int) and count == 0:
            tms = self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS * 1.5 / 1000
            self.page.wait(tms)

            challenge_view = self.page.ele("css:div[class='challenge-view']")

            cache_path = self.config.cache_dir.joinpath(f"challenge_view/_artifacts/{uuid4()}.png")
            self.screenshot_element_in_frame(challenge_view, cache_path)

            router_result = self._challenge_router(challenge_screenshot=cache_path)
            
            self._challenge_prompt = router_result.challenge_prompt

            return router_result.challenge_type

        return None

    def _wait_for_all_loaders_complete(self):
        """Wait for all loading indicators to complete (become invisible)"""
        frame_challenge = self.get_challenge_frame_locator()
        
        self.page.wait(self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS / 1000)
        
        loading_indicators = frame_challenge.eles("css:div[class='loading-indicator']")
        count = len(loading_indicators)
        
        if count == 0:
            logger.info("No load indicator found in the page")
            return True

        for loader in loading_indicators:
            wait_until(lambda: len(re.findall(r"opacity:\s*0", loader.attr('style'))), timeout=30)
            
        return True

    def get_bounding_box(self, ele: ChromiumElement) -> dict:
        left, top = ele.rect.location
        width, height = ele.rect.size
        bbox = {"x": left, "y": top, "width": width, "height": height}

        return bbox

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry request ({retry_state.attempt_number}/2) - Wait 1 second - Exception: {retry_state.outcome.exception()}"
        ),
    )
    def _capture_spatial_mapping(
        self, frame_challenge: ChromiumFrame, cache_key: Path, crumb_id: int | str
    ):
        # Capture challenge-view
        challenge_view = frame_challenge.ele("css:div[class='challenge-view']")

        challenge_screenshot = cache_key.joinpath(f"{cache_key.name}_{crumb_id}_challenge_view.png")
        self.screenshot_element_in_frame(challenge_view, challenge_screenshot)

        real_bbox = self.get_bounding_box(challenge_view)

        # Use normalized 0-1000 coordinate system for the grid overlay
        normalized_bbox = {"x": 0, "y": 0, "width": 1000, "height": 1000}

        # Save grid field
        result = create_coordinate_grid(
            challenge_screenshot,
            normalized_bbox,
            x_line_space_num=self.config.coordinate_grid.x_line_space_num,
            y_line_space_num=self.config.coordinate_grid.y_line_space_num,
            color=self.config.coordinate_grid.color,
            adaptive_contrast=self.config.coordinate_grid.adaptive_contrast,
        )

        grid_divisions = cache_key.joinpath(f"{cache_key.name}_{crumb_id}_spatial_helper.png")
        grid_divisions.parent.mkdir(parents=True, exist_ok=True)
        plt.imsave(str(grid_divisions.resolve()), result)

        return challenge_screenshot, grid_divisions, real_bbox

    def _perform_drag_drop(self, path: SpatialPath):
        """Performs a human-like drag and drop using bezier curve from mouse.py."""
        start_x, start_y = path.start_point.x, path.start_point.y
        end_x, end_y = path.end_point.x, path.end_point.y
        raw = self._raw_mouse
        cfg = self._human_cfg
        
        # Move to start position with human-like trajectory
        human_move(raw, raw.curr_x, raw.curr_y, start_x, start_y, cfg)

        # Small human reaction delay before pressing down
        sleep_ms(rand(50, 150))

        raw.down()

        # Drag along bezier path to end position
        human_move(raw, start_x, start_y, end_x, end_y, cfg)

        # Small precision adjustment pause
        sleep_ms(rand(50, 100))

        raw.up()

        # Pause between drag operations
        sleep_ms(rand(80, 120))

    def challenge_image_label_binary(self):
        frame_challenge = self.get_challenge_frame_locator()
        crumb_count = self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)
        
        for cid in range(crumb_count):
            self._wait_for_all_loaders_complete()

            # Get challenge-view
            challenge_view = frame_challenge.ele("css:div[class='challenge-view']")

            challenge_screenshot = cache_key.joinpath(f"{cache_key.name}_{cid}_challenge_view.png")
            self.screenshot_element_in_frame(challenge_view, challenge_screenshot)

            # Image classification
            response = self._image_classifier(challenge_screenshot=challenge_screenshot)
            boolean_matrix = response.convert_box_to_boolean_matrix()
            
            logger.debug(f'[{cid+1}/{crumb_count}]ToolInvokeMessage: {response.log_message}')
            self._image_classifier.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            # drive the browser to work on the challenge
            positive_cases = 0
            for i, should_be_clicked in enumerate(boolean_matrix):
                xpath_task = f"xpath://div[@class='task' and contains(@aria-label, '{i + 1}')]"
                if should_be_clicked:
                    task_image = frame_challenge.ele(xpath_task)
                    self.click_element(task_image)
                    positive_cases += 1
                elif positive_cases == 0 and i == len(boolean_matrix) - 1:
                    fallback_xpath = "xpath://div[@class='task' and contains(@aria-label, '1')]"
                    task_image = frame_challenge.ele(fallback_xpath)
                    self.click_element(task_image)

            # {{< Verify >}}
            with suppress(Exception):
                submit_btn = frame_challenge.ele("css:div[class='button-submit button']")
                self.click_element(submit_btn)
        
        return True

    def challenge_image_drag_drop(self, job_type: ChallengeTypeEnum):
        frame_challenge = self.get_challenge_frame_locator()
        crumb_count = self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)

        for cid in range(crumb_count):
            self.page.wait(self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS / 1000)

            raw, projection, real_bbox = self._capture_spatial_mapping(frame_challenge, cache_key, cid)

            user_prompt = self._match_user_prompt(job_type)

            kwargs = {}
            if job_type.value in self.config.MODEL_OVERRIDES:
                kwargs["model"] = self.config.MODEL_OVERRIDES[job_type.value]

            response = self._spatial_path_reasoner(
                challenge_screenshot=raw,
                grid_divisions=projection,
                auxiliary_information=user_prompt,
                **kwargs,
            )
            logger.debug(f'[{cid+1}/{crumb_count}]ToolInvokeMessage: {response.log_message}')
            self._spatial_path_reasoner.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            # Scale path coordinates from 0-1000 normalized space to real pixel space
            scale_x = real_bbox['width'] / 1000
            scale_y = real_bbox['height'] / 1000
            for path in response.paths:
                path.start_point.x = real_bbox['x'] + path.start_point.x * scale_x
                path.start_point.y = real_bbox['y'] + path.start_point.y * scale_y
                path.end_point.x = real_bbox['x'] + path.end_point.x * scale_x
                path.end_point.y = real_bbox['y'] + path.end_point.y * scale_y
                self._perform_drag_drop(path)

            # {{< Verify >}}
            with suppress(Exception):
                submit_btn = frame_challenge.ele("css:div[class='button-submit button']")
                self.click_element(submit_btn)

        return True

    def challenge_image_label_select(self, job_type: ChallengeTypeEnum):
        frame_challenge = self.get_challenge_frame_locator()
        crumb_count = self.check_crumb_count()
        cache_key = self.config.create_cache_key(self.captcha_payload)

        for cid in range(crumb_count):
            self.page.wait(self.config.WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS / 1000)

            raw, projection, real_bbox = self._capture_spatial_mapping(frame_challenge, cache_key, cid)

            user_prompt = self._match_user_prompt(job_type)

            kwargs = {}
            if job_type.value in self.config.MODEL_OVERRIDES:
                kwargs["model"] = self.config.MODEL_OVERRIDES[job_type.value]

            response = self._spatial_point_reasoner(
                challenge_screenshot=raw,
                grid_divisions=projection,
                auxiliary_information=user_prompt,
                **kwargs,
            )
            logger.debug(f'[{cid+1}/{crumb_count}]ToolInvokeMessage: {response.log_message}')
            self._spatial_point_reasoner.cache_response(
                path=cache_key.joinpath(f"{cache_key.name}_{cid}_model_answer.json")
            )

            # Scale model coordinates from 0-1000 normalized space to real pixel space
            scale_x = real_bbox['width'] / 1000
            scale_y = real_bbox['height'] / 1000
            for point in response.points:
                px = real_bbox['x'] + point.x * scale_x
                py = real_bbox['y'] + point.y * scale_y
                self.click_at(px, py)
                self.page.wait(0.5)

            # {{< Verify >}}
            with suppress(Exception):
                submit_btn = frame_challenge.ele("css:div[class='button-submit button']")
                self.click_element(submit_btn)

        return True