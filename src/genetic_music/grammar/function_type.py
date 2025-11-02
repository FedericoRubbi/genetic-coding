"""Function type enumerations for TidalCycles functions."""

from enum import Enum, auto

class FunctionType(Enum):
    """Shape of the function signature."""
    TERMINAL = auto()          # leaf, no children
    UNARY = auto()             # f(p)
    BINARY = auto()            # f(x, p)
    N_ARY = auto()             # f([p1, p2, ...])
    CONDITIONAL = auto()       # f(n, transform, p)
    MODIFIER = auto()          # param pattern -> ControlPattern
    TRANSFORM = auto()         # (Pattern -> Pattern)