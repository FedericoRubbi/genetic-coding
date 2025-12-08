from __future__ import annotations

"""Overlay-based mutation operator.

Wraps an existing playable pattern and a freshly generated playable
pattern in an ``overlay`` combinator.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree
from genetic_music.generator.seeds import random_seed_pattern


def overlay_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply overlay-based mutation to a pattern.

    This operator wraps the existing playable pattern and a freshly
    generated playable pattern in an ``overlay`` combinator, constructed
    purely at the tree level. It mirrors expressions like::

        overlay (p1) (p2)

    which Lark parses into a ``PatternTree`` of the form::

        control__cp_playable_term
          control__cp_binary_named
            OVERLAY "overlay"
          <left-playable>
          <right-playable>
    """
    # Existing playable branch is the current root subtree.
    left_branch = tree.root

    # Generate a fresh playable pattern for the second branch.
    new_branch_tree = random_seed_pattern(rng)
    right_branch = new_branch_tree.root

    # Randomise argument order so base/new ordering varies.
    if rng.random() < 0.5:
        first, second = left_branch, right_branch
    else:
        first, second = right_branch, left_branch

    # Build the cp_binary_named head: OVERLAY token under
    # control__cp_binary_named.
    overlay_head = TreeNode(
        op="control__cp_binary_named",
        children=[TreeNode(op="OVERLAY", value="overlay")],
    )

    # Build the cp_playable_term root that applies overlay to the two
    # branches.
    new_root = TreeNode(
        op="control__cp_playable_term",
        children=[overlay_head, first, second],
    )

    return PatternTree(root=new_root)
