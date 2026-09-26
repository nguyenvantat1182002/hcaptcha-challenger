from .base import ChallengeContext, ChallengeSolver
from .binary import BinaryLabelSolver
from .drag import DragDropSolver
from .registry import SolverRegistry
from .select import AreaSelectSolver

__all__ = [
    "AreaSelectSolver",
    "BinaryLabelSolver",
    "ChallengeContext",
    "ChallengeSolver",
    "DragDropSolver",
    "SolverRegistry",
]
