# tidal_gen/types/tidal_type.py
from enum import Enum, auto

class TidalType(Enum):
    """Semantic types in TidalCycles' DSL."""
    CONTROL = auto()          # ControlPattern
    PATTERN_BOOL = auto()
    PATTERN_INT = auto()
    PATTERN_DOUBLE = auto()
    PATTERN_NOTE = auto()
    PATTERN_STRING = auto()
    FUNC_PATTERN_TO_PATTERN = auto()
    FUNC_PATTERN_TO_CONTROL = auto()
    FUNC_CONTROL_TO_CONTROL = auto()


def unify(arg: 'TidalType', expected: 'TidalType') -> bool:
    """Return True if a type is acceptable as the expected one."""
    if arg == expected:
        return True
    # Allow ControlPattern where Pattern a is expected
    if expected.name.startswith("PATTERN") and arg == TidalType.CONTROL:
        return True
    # Generic pattern unification
    if arg.name.startswith("PATTERN") and expected.name.startswith("PATTERN"):
        return True
    return False