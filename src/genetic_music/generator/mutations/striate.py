from __future__ import annotations

"""Striate mutation operator.

Applies ``striate`` to create a stutter/layering effect.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

# MutationOp import removed - no longer needed


def striate_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply striate mutation to a pattern."""
    base_branch = tree.root

    # Choose n from 2 to 6
    n_values = [2, 3, 4, 5, 6]
    n = rng.choice(n_values)

    # Build the int parameter node
    n_node = TreeNode(
        op="control__pattern_int__int_literal",
        children=[
            TreeNode(op="control__pattern_int__INT", value=str(n)),
        ],
    )

    # Build the cp_striate_playable root
    new_root = TreeNode(
        op="control__cp_striate_playable",
        children=[
            TreeNode(op="STRIATE", value="striate"),
            TreeNode(op="LPAR", value="("),
            n_node,
            TreeNode(op="RPAR", value=")"),
            TreeNode(op="LPAR", value="("),
            base_branch,
            TreeNode(op="RPAR", value=")"),
        ],
    )

    return PatternTree(root=new_root)
