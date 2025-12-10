from __future__ import annotations

"""Shared utilities and constants for mutation operators.

This module centralises reusable pieces that multiple mutation operators
need: the :class:`MutationOp` type alias, common musical value pools, and
simple tree helpers.
"""

import random
from typing import Callable

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

# Public type alias used across mutation implementations.
MutationOp = Callable[[PatternTree, random.Random], PatternTree]


# ---------------------------------------------------------------------------
# Shared finite musical value pools
# ---------------------------------------------------------------------------

SOUND_POOL: list[str] = [
    "bd",
    "sn",
    "hh",
    # "cp",
    # "tabla",
    # "arpy",
    # "superkick",
    # "supersquare",
    # "supertron",
    # "supersaw",
    "superpiano",
]

SCALE_NAME_POOL: list[str] = [
    "major",
    "minor",
    # "dorian",
    # "ritusen",
]


# ---------------------------------------------------------------------------
# Note / scale pattern generators
# ---------------------------------------------------------------------------

# Type alias for small helpers that build pattern strings like "0 4 7".
PatternStringGenerator = Callable[[random.Random], str]


def _single_octave_pattern(
    rng: random.Random,
    *,
    degree_min: int,
    degree_max: int,
) -> str:
    """Build a space-separated pattern string confined to a single octave.

    A note-count in {2, 3, 4, 5} is chosen with uniform probability and
    distinct degrees are sampled from [degree_min, degree_max] (inclusive).
    The resulting integers are sorted so that the pattern is musically
    ascending.
    """

    # Uniform over {2, 3, 4, 5}
    length = rng.choice((2, 3, 4, 5))

    # Constrain to one "octave" of degrees.
    all_degrees = list[int](range(degree_min, degree_max + 1))
    # Guard against misconfiguration where the octave is too small.
    length = min(length, len(all_degrees))

    chosen = sorted(rng.sample(all_degrees, k=length))
    return " ".join(str(d) for d in chosen)


# For plain `n` / `note` modifiers we work directly in semitones within a
# single octave (12 semitones). This keeps all values within one octave.
NOTE_PATTERN_GENERATOR: PatternStringGenerator = (
    lambda rng: _single_octave_pattern(rng, degree_min=0, degree_max=11)
)


# For scale-based mutations we instead generate scale degrees, which
# are typically limited to the first octave of the scale. Keeping the
# range tighter than NOTE_PATTERN_GENERATOR makes the melodic contour
# interact a bit differently with the chosen scale.
SCALE_INT_PATTERN_GENERATOR: PatternStringGenerator = (
    lambda rng: _single_octave_pattern(rng, degree_min=0, degree_max=7)
)


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------

def clone_treenode(node: TreeNode) -> TreeNode:
    """Recursively clone a :class:`TreeNode` subtree.

    This helper is used by mutation operators that want to avoid mutating
    the input :class:`PatternTree` in-place.
    """

    return TreeNode(
        op=node.op,
        children=[clone_treenode(child) for child in node.children],
        value=node.value,
    )
