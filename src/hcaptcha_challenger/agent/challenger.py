# -*- coding: utf-8 -*-
# Time       : 2024/4/7 11:43
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:

import threading
import asyncio
import json
import msgpack

from queue import Queue, Empty
from contextlib import suppress
from datetime import datetime
from typing import List
from DrissionPage._pages.chromium_frame import ChromiumFrame
from loguru import logger

from hcaptcha_challenger.agent.robotic import RoboticArm
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.models import (
    CaptchaResponse,
    RequestType,
    ChallengeSignal,
    CaptchaPayload,
)


class AgentV:
    def __init__(self, page: ChromiumFrame, agent_config: AgentConfig):
        self.page = page
        self.config = agent_config

        self.robotic_arm = RoboticArm(page=page, config=agent_config)

        self._captcha_payload: CaptchaPayload | None = None
        self._captcha_payload_queue: Queue[CaptchaPayload | None] = Queue()
        self._captcha_response_queue: Queue[CaptchaResponse] = Queue()
        self.cr_list: List[CaptchaResponse] = []

        # self.page.on("response", self._task_handler)
        self.page.listen.start(['/getcaptcha', '/checkcaptcha'])
        threading.Thread(target=self._task_handler, daemon=True).start()

    def _cache_validated_captcha_response(self, cr: CaptchaResponse):
        if not cr.is_pass:
            return

        self.cr_list.append(cr)

        try:
            captcha_response = cr.model_dump(mode="json", by_alias=True)
            current_time = datetime.now().strftime("%Y%m%d/%Y%m%d%H%M%S%f")
            cache_path = self.config.captcha_response_dir.joinpath(f"{current_time}.json")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            t = json.dumps(captcha_response, indent=2, ensure_ascii=False)
            cache_path.write_text(t, encoding="utf-8")
        except Exception as err:
            logger.error(f"Saving captcha response failed - {err}")
            
    def _task_handler(self):
        for packet in self.page.listen.steps():
            if '/getcaptcha' in packet.url:
                result = self.page.run_js(f"""
                    async function() {{
                        const byteArray = new Uint8Array({list(packet.response.body)});
                        console.log('Data has been converted to Uint8Array, length:', byteArray.length);

                        try {{
                            const hswResult = await hsw(0, byteArray);
                            return Array.from(hswResult);
                        }} catch (e) {{
                            return {{error: e.toString()}};
                        }}
                    }}
                """)

                unpacked_data = msgpack.unpackb(bytes(result))
                captcha_payload = CaptchaPayload(**unpacked_data)

                self._captcha_payload_queue.put_nowait(captcha_payload)
            elif '/checkcaptcha' in packet.url:
                metadata = packet.response.body
                self._captcha_response_queue.put_nowait(CaptchaResponse(**metadata))
                
    def _review_challenge_type(self) -> RequestType | ChallengeTypeEnum:
        try:
            self._captcha_payload = self._captcha_payload_queue.get(timeout=30)
            self.page.wait(0.5)
        except asyncio.TimeoutError:
            logger.error("Wait for captcha payload to timeout")
            self._captcha_payload = None

        self.robotic_arm.signal_crumb_count = None
        self.robotic_arm.captcha_payload = None
        if not self._captcha_payload:
            return self.robotic_arm.check_challenge_type()

        try:
            request_type = self._captcha_payload.request_type
            tasklist = self._captcha_payload.tasklist
            tasklist_length = len(tasklist)
            self.robotic_arm.captcha_payload = self._captcha_payload
            match request_type:
                case RequestType.IMAGE_LABEL_BINARY:
                    self.robotic_arm.signal_crumb_count = int(tasklist_length / 9)
                    return RequestType.IMAGE_LABEL_BINARY
                case RequestType.IMAGE_LABEL_AREA_SELECT:
                    self.robotic_arm.signal_crumb_count = tasklist_length
                    max_shapes = self._captcha_payload.request_config.max_shapes_per_image
                    if not isinstance(max_shapes, int):
                        return self.robotic_arm.check_challenge_type()
                    return (
                        ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT
                        if max_shapes == 1
                        else ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT
                    )
                case RequestType.IMAGE_DRAG_DROP:
                    self.robotic_arm.signal_crumb_count = tasklist_length
                    return (
                        ChallengeTypeEnum.IMAGE_DRAG_SINGLE
                        if len(tasklist[0].entities) == 1
                        else ChallengeTypeEnum.IMAGE_DRAG_MULTI
                    )

            logger.warning(f"Unknown request_type: {request_type=}")
        except Exception as err:
            logger.error(f"Error parsing challenge type: {err}")

        # Fallback to visual recognition solution
        return self.robotic_arm.check_challenge_type()

    def _solve_captcha(self) -> ChallengeSignal:
        challenge_type = self._review_challenge_type()
        logger.debug(f"Start Challenge - type={challenge_type.value} count={self.robotic_arm.signal_crumb_count}")
        
        # {{< Skip specific challenge questions >}}
        # with suppress(Exception):
        if self.config.ignore_request_questions and self._captcha_payload:
            for q in self.config.ignore_request_questions:
                if q in self._captcha_payload.get_requester_question():
                    return False

        # {{< challenge start >}}
        match challenge_type:
            case RequestType.IMAGE_LABEL_BINARY:
                if RequestType.IMAGE_LABEL_BINARY not in self.config.ignore_request_types:
                    return self.robotic_arm.challenge_image_label_binary()
            case challenge_type.IMAGE_LABEL_SINGLE_SELECT:
                if (
                    RequestType.IMAGE_LABEL_AREA_SELECT not in self.config.ignore_request_types
                    and challenge_type.IMAGE_LABEL_SINGLE_SELECT
                    not in self.config.ignore_request_types
                ):
                    return self.robotic_arm.challenge_image_label_select(challenge_type)
            case challenge_type.IMAGE_LABEL_MULTI_SELECT:
                if (
                    RequestType.IMAGE_LABEL_AREA_SELECT not in self.config.ignore_request_types
                    and challenge_type.IMAGE_LABEL_MULTI_SELECT
                    not in self.config.ignore_request_types
                ):
                    return self.robotic_arm.challenge_image_label_select(challenge_type)
            case challenge_type.IMAGE_DRAG_SINGLE:
                if (
                    RequestType.IMAGE_DRAG_DROP not in self.config.ignore_request_types
                    and ChallengeTypeEnum.IMAGE_DRAG_SINGLE
                    not in self.config.ignore_request_types
                ):
                    return self.robotic_arm.challenge_image_drag_drop(challenge_type)
            case challenge_type.IMAGE_DRAG_MULTI:
                if (
                    RequestType.IMAGE_DRAG_DROP not in self.config.ignore_request_types
                    and ChallengeTypeEnum.IMAGE_DRAG_MULTI
                    not in self.config.ignore_request_types
                ):
                    return self.robotic_arm.challenge_image_drag_drop(challenge_type)
            # {{< HCI >}}
            case _:
                # todo Agentic Workflow | zero-shot challenge
                logger.warning(f"Unknown types of challenges: {challenge_type}")
            
        return False
        
    def wait_for_challenge(self) -> ChallengeSignal:
        # Assigning human-computer challenge tasks to the main thread coroutine.
        # ----------------------------------------------------------------------
        try:
            if self._captcha_response_queue.empty():
                result = self._solve_captcha()
                if not result:
                    return ChallengeSignal.FAILURE
        except asyncio.TimeoutError:
            logger.error("Challenge execution timed out", timeout=self.config.EXECUTION_TIMEOUT)
            return ChallengeSignal.EXECUTION_TIMEOUT

        # Waiting for hCAPTCHA response processing result
        # -----------------------------------------------
        # After the completion of the human-machine challenge workflow,
        # it is expected to obtain a signal indicating whether the challenge was successful in the cr_queue.
        logger.debug("Start checking captcha response")
        try:
            cr = self._captcha_response_queue.get(timeout=self.config.RESPONSE_TIMEOUT)
        except Empty:
            logger.error(f"Wait for captcha response timeout {self.config.RESPONSE_TIMEOUT}s")
            return ChallengeSignal.EXECUTION_TIMEOUT
        else:
            # Match: Timeout / Loss
            if not cr or not cr.is_pass:
                if self.config.RETRY_ON_FAILURE:
                    logger.warning("Failed to challenge, try to retry the strategy")
                    return self.wait_for_challenge()
                return ChallengeSignal.FAILURE
            # Match: Success
            if cr.is_pass:
                logger.success("Challenge success")
                self._cache_validated_captcha_response(cr)
                return ChallengeSignal.SUCCESS

        return ChallengeSignal.FAILURE

