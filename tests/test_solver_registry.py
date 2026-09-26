# -*- coding: utf-8 -*-
from hcaptcha_challenger.agent.solvers.base import ChallengeContext, ChallengeSolver
from hcaptcha_challenger.agent.solvers.registry import SolverRegistry
from hcaptcha_challenger.models import ChallengeTypeEnum, RequestType


class FakeSolver(ChallengeSolver):
    def __init__(self, name: str):
        self.name = name

    async def solve(self, ctx: ChallengeContext) -> None:
        pass


def test_registry_registration_and_get():
    registry = SolverRegistry()
    binary_solver = FakeSolver("binary")
    area_solver = FakeSolver("area")

    registry.register(RequestType.IMAGE_LABEL_BINARY, binary_solver)
    registry.register(
        [
            ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
            ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
        ],
        area_solver,
    )

    assert registry.get(RequestType.IMAGE_LABEL_BINARY) is binary_solver
    assert registry.get(ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT) is area_solver
    assert registry.get(ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT) is area_solver
    assert registry.get(ChallengeTypeEnum.IMAGE_DRAG_SINGLE) is None
    assert registry.get(None) is None


def test_registry_is_ignored():
    registry = SolverRegistry()

    # Empty ignore list
    assert not registry.is_ignored(RequestType.IMAGE_LABEL_BINARY, [])
    assert not registry.is_ignored(RequestType.IMAGE_LABEL_BINARY, None)

    # Direct enum match
    assert registry.is_ignored(
        RequestType.IMAGE_LABEL_BINARY, [RequestType.IMAGE_LABEL_BINARY]
    )

    # Direct value match
    assert registry.is_ignored(
        RequestType.IMAGE_LABEL_BINARY, ["image_label_binary"]
    )

    # Hierarchical Area Select ignore
    assert registry.is_ignored(
        ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
        [RequestType.IMAGE_LABEL_AREA_SELECT],
    )
    assert registry.is_ignored(
        ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
        ["image_label_area_select"],
    )

    # Hierarchical Drag Drop ignore
    assert registry.is_ignored(
        ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
        [RequestType.IMAGE_DRAG_DROP],
    )
    assert registry.is_ignored(
        ChallengeTypeEnum.IMAGE_DRAG_MULTI,
        ["image_drag_drop"],
    )

    # Not ignored
    assert not registry.is_ignored(
        ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
        [RequestType.IMAGE_LABEL_BINARY],
    )
