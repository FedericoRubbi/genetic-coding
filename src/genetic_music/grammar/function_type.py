"""Function type enumerations for TidalCycles functions."""

from enum import Enum

class FunctionType(Enum):
    """Types of TidalCycles function signatures."""
    UNARY = "unary"  # (pattern) -> pattern
    BINARY_NUMERIC = "binary_numeric"  # (number, pattern) -> pattern
    BINARY_INT = "binary_int"  # (int, pattern) -> pattern
    N_ARY = "n_ary"  # (pattern, pattern, ...) -> pattern
    CONDITIONAL = "conditional"  # (int, pattern, pattern) -> pattern
    PROBABILISTIC = "probabilistic"  # (float[0-1], pattern) -> pattern