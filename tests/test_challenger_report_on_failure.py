# -*- coding: utf-8 -*-
from unittest.mock import AsyncMock, MagicMock
import asyncio
import pytest

from hcaptcha_challenger.agent.challenger import AgentV
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.agent.solvers.base import ChallengeContext, ChallengeSolver
from hcaptcha_challenger.models import CaptchaResponse, ChallengeSignal


class DummySolver(ChallengeSolver):
    def __init__(self, client=None):
        self._yescaptcha_client = client

    async def solve(self, ctx: ChallengeContext) -> None:
        pass


@pytest.mark.asyncio
async def test_solver_report_feedback_delegates_to_client():
    mock_client = AsyncMock()
    mock_client.report_recent_tasks = AsyncMock()
    mock_client.clear_recent_tasks = MagicMock()

    solver = DummySolver(client=mock_client)

    await solver.report_feedback(is_correct=False)
    mock_client.report_recent_tasks.assert_awaited_once_with(is_correct=False)

    solver.clear_feedback()
    mock_client.clear_recent_tasks.assert_called_once()


@pytest.mark.asyncio
async def test_challenger_reports_feedback_on_failure():
    mock_page = MagicMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.on = MagicMock()

    config = AgentConfig(
        RETRY_ON_FAILURE=False,
        EXECUTION_TIMEOUT=5.0,
        RESPONSE_TIMEOUT=5.0,
    )

    agent = AgentV(page=mock_page, agent_config=config)

    # Attach dummy active solver with mock report_feedback
    mock_solver = AsyncMock(spec=ChallengeSolver)
    mock_solver.report_feedback = AsyncMock()
    mock_solver.clear_feedback = MagicMock()
    agent._active_solver = mock_solver

    # Create a failed response
    failed_cr = CaptchaResponse(**{"pass": False, "generated_pass_UUID": ""})
    await agent._captcha_response_queue.put(failed_cr)

    # Execute wait_for_challenge
    signal = await agent.wait_for_challenge()

    assert signal == ChallengeSignal.FAILURE
    mock_solver.report_feedback.assert_awaited_once_with(is_correct=False)
    mock_solver.clear_feedback.assert_not_called()


@pytest.mark.asyncio
async def test_challenger_clears_feedback_on_success():
    mock_page = MagicMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.on = MagicMock()

    config = AgentConfig(
        RETRY_ON_FAILURE=False,
        EXECUTION_TIMEOUT=5.0,
        RESPONSE_TIMEOUT=5.0,
    )

    agent = AgentV(page=mock_page, agent_config=config)

    mock_solver = AsyncMock(spec=ChallengeSolver)
    mock_solver.report_feedback = AsyncMock()
    mock_solver.clear_feedback = MagicMock()
    agent._active_solver = mock_solver

    # Create a success response
    success_cr = CaptchaResponse(**{"pass": True, "generated_pass_UUID": "valid_uuid"})
    await agent._captcha_response_queue.put(success_cr)

    signal = await agent.wait_for_challenge()

    assert signal == ChallengeSignal.SUCCESS
    mock_solver.report_feedback.assert_not_called()
    mock_solver.clear_feedback.assert_called_once()
