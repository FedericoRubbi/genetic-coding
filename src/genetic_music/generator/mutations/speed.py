from __future__ import annotations

"""Speed mutation operator (fast/slow)."""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree


def speed_change(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply a speed transformation (``fast`` or ``slow``) to the pattern.

    The tree structure follows::

    control__cp_playable_term
      control__prefix_cp
        FAST/SLOW token
        control__pattern_time__INT or control__pattern_time__DOUBLE (factor)
      <base_playable_subtree>
    """
    base_branch = tree.root

    # Choose fast or slow
    op_name = rng.choice(["fast", "slow"])

    # Choose factor from sensible values
    factors = [0.5, 1.5, 2, 3]
    factor = rng.choice(factors)

    # Build the prefix_cp node with the appropriate token and factor
    if op_name == "fast":
        op_token = TreeNode(op="FAST", value="fast")
    else:  # "slow"
        op_token = TreeNode(op="SLOW", value="slow")

        # Determine if factor is int or float, and create appropriate node
    if isinstance(factor, int) or factor == int(factor):
        factor_node = TreeNode(
            op="control__pattern_time__INT",
            value=str(int(factor)),
        )
    else:
        factor_node = TreeNode(
            op="control__pattern_time__DOUBLE",
            value=str(factor),
        )

    prefix_node = TreeNode(
        op="control__prefix_cp",
        children=[op_token, factor_node],
    )

    # Build the cp_playable_term root that applies the speed transformation
    new_root = TreeNode(
        op="control__cp_playable_term",
        children=[prefix_node, base_branch],
    )

    return PatternTree(root=new_root)
