from __future__ import annotations

"""Append / fastAppend mutation operator.

Creates a new pattern by appending a randomly generated pattern using the
``append`` / ``fastAppend`` combinators.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import MutationOp


def append_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
) -> MutationOp:
    """Tree-level append/fastAppend mutation operator.

    This mirrors expressions like::

        append (p1) (p2)
        fastAppend (p1) (p2)

    which Lark parses into a ``PatternTree`` of the form::

        control__cp_playable_term
          control__cp_binary_named
            APPEND | FASTAPPEND
          <left-playable>
          <right-playable>

    Semantics:

    - combinator is randomly chosen between ``append`` and
      ``fastAppend``,
    - argument order is randomized, so either the base or the new branch
      can appear on the left.
    """

    # Unused config parameters kept for future tuning.
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Local import to avoid circular imports at module import time.
        from genetic_music.generator.generation import generate_expressions

        # Existing playable branch is the current root subtree.
        base_branch = tree.root

        # Generate 1–3-depth new branch as a fresh playable pattern.
        new_branch_tree = generate_expressions(rng.randint(1, 3))[0]
        new_branch_branch = new_branch_tree.root

        # Choose combinator: 'append' or 'fastAppend'.
        combinator = "append" if rng.random() < 0.5 else "fastAppend"

        # Randomize argument order.
        if rng.random() < 0.5:
            left, right = base_branch, new_branch_branch
        else:
            left, right = new_branch_branch, base_branch

        # Build the cp_binary_named head with the appropriate token.
        if combinator == "append":
            head_token = TreeNode(op="APPEND", value="append")
        else:  # "fastAppend"
            head_token = TreeNode(op="FASTAPPEND", value="fastAppend")

        binary_head = TreeNode(
            op="control__cp_binary_named",
            children=[head_token],
        )

        # Build the cp_playable_term root that applies the combinator.
        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[binary_head, left, right],
        )

        return PatternTree(root=new_root)

    return op
