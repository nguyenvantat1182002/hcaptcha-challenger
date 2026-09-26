from collections.abc import Sequence

from hcaptcha_challenger.agent.solvers.base import ChallengeSolver
from hcaptcha_challenger.models import ChallengeTypeEnum, RequestType


class SolverRegistry:
    """
    Central dispatch registry that maps challenge types to their registered solver implementations
    and enforces challenge-filtering rules.
    """

    def __init__(self):
        self._solvers: dict[ChallengeTypeEnum | RequestType, ChallengeSolver] = {}

    def register(
        self,
        challenge_types: ChallengeTypeEnum | RequestType | Sequence[ChallengeTypeEnum | RequestType],
        solver: ChallengeSolver,
    ) -> None:
        """
        Registers a solver for one or more challenge types.
        """
        if isinstance(challenge_types, (ChallengeTypeEnum, RequestType)):
            challenge_types = [challenge_types]
        for c_type in challenge_types:
            self._solvers[c_type] = solver

    def get(
        self, challenge_type: ChallengeTypeEnum | RequestType | None
    ) -> ChallengeSolver | None:
        """
        Retrieves the registered solver for the given challenge type.
        """
        if challenge_type is None:
            return None
        return self._solvers.get(challenge_type)

    @staticmethod
    def is_ignored(
        challenge_type: ChallengeTypeEnum | RequestType | None,
        ignore_request_types: Sequence[ChallengeTypeEnum | RequestType | str] | None,
    ) -> bool:
        """
        Checks whether the challenge type should be ignored according to configuration.
        """
        if not ignore_request_types or challenge_type is None:
            return False

        # Direct match (by enum or value)
        if (
            challenge_type in ignore_request_types
            or getattr(challenge_type, "value", None) in ignore_request_types
        ):
            return True

        # Hierarchical match: Area Select
        if (
            challenge_type
            in (
                ChallengeTypeEnum.IMAGE_LABEL_SINGLE_SELECT,
                ChallengeTypeEnum.IMAGE_LABEL_MULTI_SELECT,
            )
            and (
                RequestType.IMAGE_LABEL_AREA_SELECT in ignore_request_types
                or RequestType.IMAGE_LABEL_AREA_SELECT.value in ignore_request_types
            )
        ):
            return True

        # Hierarchical match: Drag Drop
        if (
            challenge_type
            in (
                ChallengeTypeEnum.IMAGE_DRAG_SINGLE,
                ChallengeTypeEnum.IMAGE_DRAG_MULTI,
            )
            and (
                RequestType.IMAGE_DRAG_DROP in ignore_request_types
                or RequestType.IMAGE_DRAG_DROP.value in ignore_request_types
            )
        ):
            return True

        return False
