# tidal_gen/grammar/registry.py
from .function_signature import FunctionSignature
from .tidal_type import TidalType
from .function_type import FunctionType
import random

FUNCTIONS = [
    # --- Sound sources (ControlPattern)
    FunctionSignature("sound", FunctionType.TERMINAL, [], TidalType.CONTROL),
    # FunctionSignature("silence", FunctionType.TERMINAL, [], TidalType.CONTROL),

    # --- Unary ControlPattern transforms
    FunctionSignature("rev", FunctionType.UNARY, [TidalType.CONTROL], TidalType.CONTROL),
    FunctionSignature("brak", FunctionType.UNARY, [TidalType.CONTROL], TidalType.CONTROL),

    # --- Binary numeric transforms
    FunctionSignature("fast", FunctionType.BINARY,
        [TidalType.PATTERN_DOUBLE, TidalType.CONTROL], TidalType.CONTROL,
        param_generator=lambda: random.uniform(0.5, 4.0)),

    # --- Probabilistic transform
    FunctionSignature("degradeBy", FunctionType.BINARY,
        [TidalType.PATTERN_DOUBLE, TidalType.CONTROL], TidalType.CONTROL,
        param_generator=lambda: random.uniform(0.2, 0.8)),

    # --- Combinators
    FunctionSignature("stack", FunctionType.N_ARY,
        [TidalType.CONTROL], TidalType.CONTROL),
    FunctionSignature("cat", FunctionType.N_ARY,
        [TidalType.CONTROL], TidalType.CONTROL),

    # --- Modifiers
    FunctionSignature("speed", FunctionType.MODIFIER,
        [TidalType.PATTERN_DOUBLE, TidalType.CONTROL], TidalType.CONTROL),
    FunctionSignature("pan", FunctionType.MODIFIER,
        [TidalType.PATTERN_DOUBLE, TidalType.CONTROL], TidalType.CONTROL),
]