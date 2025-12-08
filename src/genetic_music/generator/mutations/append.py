from __future__ import annotations

"""Append / fastAppend mutation operator.

Creates a new pattern by appending a randomly generated pattern using the
``append`` / ``fastAppend`` combinators.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree
from genetic_music.generator.seeds import random_seed_pattern


def append_pattern(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply append/fastAppend mutation to a pattern.

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
    # Existing playable branch is the current root subtree.
    base_branch = tree.root

    # Generate a fresh simple playable pattern.
    new_branch_tree = random_seed_pattern(rng)
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
