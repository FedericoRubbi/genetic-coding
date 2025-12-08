from __future__ import annotations

"""Seed pattern generation and shared musical value pools.

This module defines small seed patterns and the finite pools of musical
values (sounds, note patterns, scales) used both by seed generation and
by mutation operators.
"""

import random
from typing import List

from genetic_music.tree.pattern_tree import PatternTree

from .parser import parse_control_pattern

# ---------------------------------------------------------------------------
# Shared finite musical value pools
# ---------------------------------------------------------------------------

SOUND_POOL: List[str] = ["bd", "sn", "hh", "cp", "tabla", "arpy"]

NOTE_PATTERN_POOL: List[str] = [
    "0",
    "0 7",
    "0 4 7",
    "0 2 4 5 7 9 11",
    "0 .. 11",
    "-12 .. 12",
    "24 36 48",
    "60",
    "60 64 67",
    "0.5",
    "1.5",
]

SCALE_NAME_POOL: List[str] = ["major", "minor", "dorian", "ritusen"]

SCALE_INT_PATTERN_POOL: List[str] = ["0", "0 2 4", "0 .. 7"]


# ---------------------------------------------------------------------------
# Seed pattern generation
# ---------------------------------------------------------------------------


def random_seed_pattern(rng: random.Random) -> PatternTree:
    """Generate a small, simple seed pattern as a :class:`PatternTree`.

    Seeds are intentionally tiny (single sounds, simple note patterns, or
    short stacks) and are later grown by applying tree-level mutation
    operators in :func:`genetic_music.generator.generation.generate_expressions_mutational`.
    """

    # Simple families of seed patterns
    seed_kind = rng.choice(["sound", "note", "stack"])

    if seed_kind == "sound":
        sound = rng.choice(SOUND_POOL)
        code = f's("{sound}")'
    elif seed_kind == "note":
        sound = rng.choice(SOUND_POOL)
        note_pattern = rng.choice(NOTE_PATTERN_POOL)
        code = f's("{sound}") # n "{note_pattern}"'
    else:  # "stack"
        # 2–3 simple sound atoms stacked together
        k = rng.randint(2, 3)
        sounds = [rng.choice(SOUND_POOL) for _ in range(k)]
        inner = ",".join(f's("{s}")' for s in sounds)
        code = f"stack[{inner}]"

    try:
        tree = parse_control_pattern(code)
        return PatternTree.from_lark_tree(tree)
    except Exception:
        # Fallback: if parsing fails for any reason, fall back to a very
        # simple seed.
        fallback_tree = parse_control_pattern('s("bd")')
        return PatternTree.from_lark_tree(fallback_tree)
