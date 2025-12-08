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

SOUND_POOL: list[str] = ["bd", "sn", "hh", "cp", "tabla", "arpy"]

NOTE_PATTERN_POOL: list[str] = [
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

SCALE_NAME_POOL: list[str] = ["major", "minor", "dorian", "ritusen"]

SCALE_INT_PATTERN_POOL: list[str] = ["0", "0 2 4", "0 .. 7"]


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
