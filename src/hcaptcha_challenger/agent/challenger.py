# Time       : 2024/4/7 11:43
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:
import asyncio
import json
import httpx
import msgpack

from asyncio import Queue
from contextlib import suppress
from datetime import datetime
from loguru import logger
from playwright.async_api import Frame, Locator, Page, Response

from hcaptcha_challenger.agent.config import (
    AgentConfig,
)
from hcaptcha_challenger.agent.driver import BrowserArm
from hcaptcha_challenger.agent.pointer import (
    HumanoidPointer,
)
from hcaptcha_challenger.agent.solvers import (
    AreaSelectSolver,
    BinaryLabelSolver,
    ChallengeContext,
    ChallengeSolver,
    DragDropSolver,
    SolverRegistry,
)
from hcaptcha_challenger.models import (
    CaptchaPayload,
    CaptchaResponse,
    ChallengeSignal,
    ChallengeTypeEnum,
    RequestType,
)


from hcaptcha_challenger.agent.robotic_arm import RoboticArm


class AgentV:
    def __init__(self, page: Page, agent_config: AgentConfig):
        self.page = page
        self.config = agent_config

        self.pointer = HumanoidPointer(
            page=page, disable_bezier_trajectory=agent_config.DISABLE_BEZIER_TRAJECTORY
        )
        self.arm = BrowserArm(page=page, config=agent_config, pointer=self.pointer)

        # Initialize solver registry and register concrete solvers
        self.solver_registry = SolverRegistry()
        self._init_solvers()

        # Backward compatibility facade
        self.robotic_arm = RoboticArm(
            page=page,
            config=agent_config,
            arm=self.arm,
            pointer=self.pointer,
            registry=self.solver_registry,
        )

        self._captcha_payload: CaptchaPayload | None = None
        self._captcha_payload_queue: Queue[CaptchaPayload | None] = Queue()
        self._captcha_response_queue: Queue[CaptchaResponse] = Queue()
        self.cr_list: list[CaptchaResponse] = []
        self._active_solver: ChallengeSolver | None = None

        self.page.on("response", self._task_handler)

    def _init_solvers(self):
        binary_solver = BinaryLabelSolver(
            config=self.config, driver=self.arm, pointer=self.pointer
        )
        select_solver = AreaSelectSolver(
            config=self.config, driver=self.arm, pointer=self.pointer
        )
        drag_solver = DragDropSolver(
            config=self.config, driver=self.arm, pointer=self.pointer
        )

        self.solver_registry.register(RequestType.IMAGE_LABEL_BINARY, binary_solver)
        self.solver_registry.register(
            [
                ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
                ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
            ],
            select_solver,
        )
        self.solver_registry.register(
            [
                ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
                ChallengeTypeEnum.IMAGE_DRAG_MULTI,
            ],
            drag_solver,
        )

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

    @logger.catch
    async def _task_handler(self, response: Response):
        if response.url.endswith("/hsw.js"):
            try:
                async with httpx.AsyncClient(headers=response.headers, timeout=30) as client:
                    hsw_text = await client.get(response.url)
                    hsw_text = hsw_text.text
                await self.page.evaluate(hsw_text)
                await self.page.evaluate("""
                    () => {
                        return typeof hsw === 'function' ? true : 'hsw不是函数';
                    }
                    """)
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
                    logger.warning("HSW reverse disabled by config, fallback to regular processing")
                    self._captcha_payload_queue.put_nowait(None)
                    return

                has_hsw = await self.page.evaluate("""
                    () => {
                        return typeof hsw === 'function' ? true : false;
                    }
                    """)

                if has_hsw:
                    result = await self.page.evaluate(f"""
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
                        """)
                        
                    if isinstance(result, list) and not any(
                        isinstance(x, dict) and "error" in x for x in result
                    ):
                        unpacked_data: dict = msgpack.unpackb(bytes(result))
                        if unpacked_data.get('pass'):
                            while not self._captcha_response_queue.empty():
                                self._captcha_response_queue.get_nowait()
                            cr = CaptchaResponse(**unpacked_data)
                            self._captcha_response_queue.put_nowait(cr)
                        else:
                            captcha_payload = CaptchaPayload(**unpacked_data)
                            self._captcha_payload_queue.put_nowait(captcha_payload)
                        return
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

        self.arm.signal_crumb_count = None
        self.robotic_arm.signal_crumb_count = None
        self.robotic_arm.captcha_payload = self._captcha_payload

        if not self._captcha_payload:
            return await self.arm.check_challenge_type()

        try:
            request_type = self._captcha_payload.request_type
            tasklist = self._captcha_payload.tasklist
            tasklist_length = len(tasklist)

            match request_type:
                case RequestType.IMAGE_LABEL_BINARY:
                    self.arm.signal_crumb_count = int(tasklist_length / 9)
                    self.robotic_arm.signal_crumb_count = self.arm.signal_crumb_count
                    return RequestType.IMAGE_LABEL_BINARY
                case RequestType.IMAGE_LABEL_AREA_SELECT:
                    self.arm.signal_crumb_count = tasklist_length
                    self.robotic_arm.signal_crumb_count = self.arm.signal_crumb_count
                    max_shapes = self._captcha_payload.request_config.max_shapes_per_image
                    if not isinstance(max_shapes, int):
                        return await self.arm.check_challenge_type()
                    return (
                        ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT
                        if max_shapes == 1
                        else ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT
                    )
                case RequestType.IMAGE_DRAG_DROP:
                    self.arm.signal_crumb_count = tasklist_length
                    self.robotic_arm.signal_crumb_count = self.arm.signal_crumb_count
                    return (
                        ChallengeTypeEnum.IMAGE_DRAG_SINGLE
                        if len(tasklist[0].entities) == 1
                        else ChallengeTypeEnum.IMAGE_DRAG_MULTI
                    )

            logger.warning(f"Unknown request_type: {request_type=}")
        except Exception as err:
            logger.error(f"Error parsing challenge type: {err}")

        # Fallback to visual recognition solution
        return await self.arm.check_challenge_type()

    async def _solve_captcha(self):
        challenge_type = await self._review_challenge_type()
        crumb_count = await self.arm.check_crumb_count()
        type_str = getattr(challenge_type, "value", str(challenge_type))
        logger.debug(f"Start Challenge - type={type_str} count={crumb_count}")

        try:
            # {{< Skip specific challenge questions >}}
            with suppress(Exception):
                if self.config.ignore_request_questions and self._captcha_payload:
                    for q in self.config.ignore_request_questions:
                        if q in self._captcha_payload.get_requester_question():
                            await self.page.wait_for_timeout(2000)
                            await self.arm.refresh_challenge()
                            return await self._solve_captcha()

            # Check if challenge type is filtered out
            if self.solver_registry.is_ignored(
                challenge_type, self.config.ignore_request_types
            ):
                logger.info(f"Ignoring challenge type: {challenge_type}")
            else:
                solver = self.solver_registry.get(challenge_type)
                if solver:
                    self._active_solver = solver
                    frame = await self.arm.get_challenge_frame_locator()
                    if frame:
                        cache_key = self.config.create_cache_key(self._captcha_payload)
                        ctx = ChallengeContext(
                            frame=frame,
                            crumb_count=crumb_count,
                            cache_key=cache_key,
                            payload=self._captcha_payload,
                            job_type=challenge_type,
                        )
                        return await solver.solve(ctx)
                else:
                    # todo Agentic Workflow | zero-shot challenge
                    logger.warning(f"Unknown types of challenges: {challenge_type}")

            await self.page.wait_for_timeout(2000)
            await self.arm.refresh_challenge()
            return await self._solve_captcha()
        except Exception as err:
            logger.exception(f"ChallengeException - type={type_str} {err=}")
            await self.page.wait_for_timeout(5000)
            await self.arm.refresh_challenge()
            return await self._solve_captcha()

    async def wait_for_challenge(self) -> ChallengeSignal:
        try:
            if self._captcha_response_queue.empty():
                await asyncio.wait_for(
                    self._solve_captcha(), timeout=self.config.EXECUTION_TIMEOUT
                )
        except asyncio.TimeoutError:
            logger.error("Challenge execution timed out", timeout=self.config.EXECUTION_TIMEOUT)
            return ChallengeSignal.EXECUTION_TIMEOUT

        logger.debug("Start checking captcha response")
        try:
            cr = await asyncio.wait_for(
                self._captcha_response_queue.get(), timeout=self.config.RESPONSE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Wait for captcha response timeout {self.config.RESPONSE_TIMEOUT}s")
            return ChallengeSignal.EXECUTION_TIMEOUT
        else:
            if not cr or not cr.is_pass:
                if self._active_solver:
                    await self._active_solver.report_feedback(is_correct=False)
                if self.config.RETRY_ON_FAILURE:
                    logger.warning("Failed to challenge, try to retry the strategy")
                    await self.page.wait_for_timeout(2000)
                    return await self.wait_for_challenge()
                return ChallengeSignal.FAILURE
            if cr.is_pass:
                logger.success("Challenge success")
                if self._active_solver:
                    self._active_solver.clear_feedback()
                self._cache_validated_captcha_response(cr)
                return ChallengeSignal.SUCCESS

        return ChallengeSignal.FAILURE
