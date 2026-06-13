# -*- coding: utf-8 -*-
# Time       : 2024/4/7 11:43
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:
import asyncio
import json
from asyncio import Queue
from contextlib import suppress
from datetime import datetime
from typing import List

import msgpack
from loguru import logger
from playwright.async_api import Page, Response

from hcaptcha_challenger.models import CaptchaResponse, RequestType, ChallengeSignal, CaptchaPayload
from hcaptcha_challenger.models import ChallengeTypeEnum
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.robotic_arm import RoboticArm


class AgentV:
    def __init__(self, page: Page, agent_config: AgentConfig, skip_url_keywords: List[str] | None = None):
        self.page = page
        self.config = agent_config
        self.skip_url_keywords = skip_url_keywords

        self.robotic_arm = RoboticArm(page=page, config=agent_config)

        self._captcha_payload: CaptchaPayload | None = None
        self._captcha_payload_queue: Queue[CaptchaPayload | None] = Queue()
        self._captcha_response_queue: Queue[CaptchaResponse] = Queue()
        self.cr_list: List[CaptchaResponse] = []

        self.page.on("response", self._task_handler)

    def _cache_validated_captcha_response(self, cr: CaptchaResponse):
        if not cr.is_pass:
            return

        self.cr_list.append(cr)

        if not self.config.ENABLE_CAPTCHA_CACHE:
            return

        try:
            captcha_response = cr.model_dump(mode="json", by_alias=True)
            current_time = datetime.now().strftime("%Y%m%d/%Y%m%d%H%M%S%f")
            cache_path = self.config.captcha_response_dir.joinpath(
                f"{current_time}.json"
            )
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            t = json.dumps(captcha_response, indent=2, ensure_ascii=False)
            cache_path.write_text(t, encoding="utf-8")
        except Exception as err:
            logger.error(f"Saving captcha response failed - {err}")

    @logger.catch
    async def _task_handler(self, response: Response):
        if self.skip_url_keywords and any(kw in response.url for kw in self.skip_url_keywords):
            if not getattr(self, "_skip_notified", False):
                logger.debug(f"Skipping challenge because URL matched skip_url_keywords: {response.url}")
                self._skip_notified = True
                self._captcha_payload_queue.put_nowait(None)
                self._captcha_response_queue.put_nowait(CaptchaResponse(error="skipped_by_url_keyword", is_pass=True))
            return

        if response.url.endswith("/hsw.js"):
            try:
                api_response = await self.page.request.get(response.url)
                hsw_text = await api_response.text()
                await self.page.evaluate(hsw_text)
            except Exception as err:
                logger.error(f"An error occurred while injecting hsw script: {err}")
        elif "/getcaptcha/" in response.url:
            self._captcha_payload = None

            # Content-Type: application/json
            if response.headers.get("content-type", "") == "application/json":
                data = await response.json()
                if data.get("pass"):
                    while not self._captcha_response_queue.empty():
                        self._captcha_response_queue.get_nowait()
                    cr = CaptchaResponse(**data)
                    self._captcha_response_queue.put_nowait(cr)
                    return
                if data.get("request_config"):
                    captcha_payload = CaptchaPayload(**data)
                    self._captcha_payload_queue.put_nowait(captcha_payload)
                    return

            # Content-Type: stream
            try:
                raw_data = await response.body()

                # [DEBUG] Force fallback to visual recognition for testing
                if self.config.DISABLE_HSW_REVERSE:
                    logger.warning(
                        "HSW reverse disabled by config, fallback to regular processing"
                    )
                    self._captcha_payload_queue.put_nowait(None)
                    return

                has_hsw = await self.page.evaluate(
                    """
                    () => {
                        return typeof hsw === 'function' ? true : false;
                    }
                    """
                )

                if has_hsw:
                    result = await self.page.evaluate(
                        f"""
                        async () => {{
                            const byteArray = new Uint8Array({list(raw_data)});
                            console.log('Data has been converted to Uint8Array, length:', byteArray.length);

                            try {{
                                const hswResult = await hsw(0, byteArray);
                                return Array.from(hswResult);
                            }} catch (e) {{
                                return {{error: e.toString()}};
                            }}
                        }}
                        """
                    )

                    if isinstance(result, list) and not any(
                        isinstance(x, dict) and "error" in x for x in result
                    ):
                        unpacked_data = msgpack.unpackb(bytes(result))
                        captcha_payload = CaptchaPayload(**unpacked_data)
                        self._captcha_payload_queue.put_nowait(captcha_payload)

                        return
                # If the reverse fails, fall back to the original process
                else:
                    logger.warning("HSW reverse failed, fallback to regular processing")
                    self._captcha_payload_queue.put_nowait(None)
            except Exception as err:
                logger.error(f"Reverse processing getcaptcha failed: {err}")
                self._captcha_payload_queue.put_nowait(None)
        elif "/checkcaptcha/" in response.url:
            try:
                metadata = await response.json()
                self._captcha_response_queue.put_nowait(CaptchaResponse(**metadata))
            except Exception as err:
                logger.exception(err)

    async def _review_challenge_type(self) -> RequestType | ChallengeTypeEnum:
        try:
            self._captcha_payload = await asyncio.wait_for(
                self._captcha_payload_queue.get(), timeout=30.0
            )
            await self.page.wait_for_timeout(500)
        except asyncio.TimeoutError:
            logger.error("Wait for captcha payload to timeout")
            self._captcha_payload = None

        if getattr(self, "_skip_notified", False):
            return "SKIP"

        self.robotic_arm.signal_crumb_count = None
        self.robotic_arm.captcha_payload = None
        if not self._captcha_payload:
            return await self.robotic_arm.check_challenge_type()

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
                    max_shapes = (
                        self._captcha_payload.request_config.max_shapes_per_image
                    )
                    if not isinstance(max_shapes, int):
                        return await self.robotic_arm.check_challenge_type()
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
        
        return "SKIP"

    async def _solve_captcha(self):
        challenge_type = await self._review_challenge_type()
        if challenge_type == "SKIP":
            return
        
        model_name = "unknown"
        if challenge_type == RequestType.IMAGE_LABEL_BINARY:
            model_name = self.config.IMAGE_CLASSIFIER_MODEL
        elif challenge_type in (ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT, ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT):
            model_name = self.config.SPATIAL_POINT_REASONER_MODEL
        elif challenge_type in (ChallengeTypeEnum.IMAGE_DRAG_SINGLE, ChallengeTypeEnum.IMAGE_DRAG_MULTI):
            model_name = self.config.SPATIAL_PATH_REASONER_MODEL

        logger.debug(
            f"Start Challenge - type={challenge_type.value} count={self.robotic_arm.signal_crumb_count} provider={self.config.active_provider} model={model_name}"
        )

        try:
            # {{< Skip specific challenge questions >}}
            with suppress(Exception):
                if self.config.ignore_request_questions and self._captcha_payload:
                    for q in self.config.ignore_request_questions:
                        if q in self._captcha_payload.get_requester_question():
                            await self.page.wait_for_timeout(2000)
                            if not await self.robotic_arm.refresh_challenge():
                                self._captcha_response_queue.put_nowait(CaptchaResponse(error="refresh_failed", is_pass=False))
                                return
                            return await self._solve_captcha()

            # {{< challenge start >}}
            match challenge_type:
                case RequestType.IMAGE_LABEL_BINARY:
                    if (
                        RequestType.IMAGE_LABEL_BINARY
                        not in self.config.ignore_request_types
                    ):
                        return await self.robotic_arm.challenge_image_label_binary()
                case challenge_type.IMAGE_LABEL_SINGLE_SELECT:
                    if (
                        RequestType.IMAGE_LABEL_AREA_SELECT
                        not in self.config.ignore_request_types
                        and challenge_type.IMAGE_LABEL_SINGLE_SELECT
                        not in self.config.ignore_request_types
                    ):
                        return await self.robotic_arm.challenge_image_label_select(
                            challenge_type
                        )
                case challenge_type.IMAGE_LABEL_MULTI_SELECT:
                    if (
                        RequestType.IMAGE_LABEL_AREA_SELECT
                        not in self.config.ignore_request_types
                        and challenge_type.IMAGE_LABEL_MULTI_SELECT
                        not in self.config.ignore_request_types
                    ):
                        return await self.robotic_arm.challenge_image_label_select(
                            challenge_type
                        )
                case challenge_type.IMAGE_DRAG_SINGLE:
                    if (
                        RequestType.IMAGE_DRAG_DROP
                        not in self.config.ignore_request_types
                        and ChallengeTypeEnum.IMAGE_DRAG_SINGLE
                        not in self.config.ignore_request_types
                    ):
                        return await self.robotic_arm.challenge_image_drag_drop(
                            challenge_type
                        )
                case challenge_type.IMAGE_DRAG_MULTI:
                    if (
                        RequestType.IMAGE_DRAG_DROP
                        not in self.config.ignore_request_types
                        and ChallengeTypeEnum.IMAGE_DRAG_MULTI
                        not in self.config.ignore_request_types
                    ):
                        return await self.robotic_arm.challenge_image_drag_drop(
                            challenge_type
                        )
                # {{< HCI >}}
                case _:
                    # todo Agentic Workflow | zero-shot challenge
                    logger.warning(f"Unknown types of challenges: {challenge_type}")
            # {{< challenge end >}}

            await self.page.wait_for_timeout(2000)
            if not await self.robotic_arm.refresh_challenge():
                self._captcha_response_queue.put_nowait(CaptchaResponse(error="refresh_failed", is_pass=False))
                return
            return await self._solve_captcha()
        except Exception as err:
            # This is an execution error inside the challenge,
            # hcaptcha challenge does not automatically refresh
            logger.exception(f"ChallengeException - type={challenge_type.value} {err=}")
            await self.page.wait_for_timeout(5000)
            if not await self.robotic_arm.refresh_challenge():
                self._captcha_response_queue.put_nowait(CaptchaResponse(error="refresh_failed", is_pass=False))
                return
            return await self._solve_captcha()

    async def wait_for_challenge(self) -> ChallengeSignal:
        # Assigning human-computer challenge tasks to the main thread coroutine.
        # ----------------------------------------------------------------------
        try:
            if self._captcha_response_queue.empty():
                await asyncio.wait_for(
                    self._solve_captcha(), timeout=self.config.EXECUTION_TIMEOUT
                )
        except asyncio.TimeoutError:
            logger.error(
                "Challenge execution timed out", timeout=self.config.EXECUTION_TIMEOUT
            )
            return ChallengeSignal.EXECUTION_TIMEOUT

        # Waiting for hCAPTCHA response processing result
        # -----------------------------------------------
        # After the completion of the human-machine challenge workflow,
        # it is expected to obtain a signal indicating whether the challenge was successful in the cr_queue.
        logger.debug("Start checking captcha response")
        try:
            cr = await asyncio.wait_for(
                self._captcha_response_queue.get(), timeout=self.config.RESPONSE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Wait for captcha response timeout {self.config.RESPONSE_TIMEOUT}s"
            )
            return ChallengeSignal.EXECUTION_TIMEOUT
        else:
            # Match: Timeout / Loss
            if not cr or not cr.is_pass:
                self.robotic_arm.report_challenge_failure()
                if self.config.RETRY_ON_FAILURE:
                    logger.warning("Failed to challenge, try to retry the strategy")
                    await self.page.wait_for_timeout(2000)
                    return await self.wait_for_challenge()
                return ChallengeSignal.FAILURE
            # Match: Success
            if cr.is_pass:
                logger.success("Challenge success")
                self._cache_validated_captcha_response(cr)
                return ChallengeSignal.SUCCESS

        return ChallengeSignal.FAILURE
