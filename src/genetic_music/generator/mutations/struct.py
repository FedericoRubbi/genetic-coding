from __future__ import annotations

"""Struct/mask-based mutation operator.

Wraps an existing playable pattern inside a Tidal ``struct`` expression
that applies a boolean mask to control timing.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

# MutationOp import removed - no longer needed


# Functions used to create valid "mask" patterns for the ``struct``
# operator that define when events are allowed to occur.
MASK_GENERATORS = [
    # Boolean mask t(a,b): a pulses across b positions (not yet in grammar)
    # lambda rng: f"t({rng.randint(2,8)},{rng.choice([8,12,16])})",
    # Boolean string mask (e.g. "t f t f f t t f f")
    lambda rng: '"' + " ".join(
    rng.choice(["t", "f"]) for _ in range(rng.randint(4, 16))
    )
    + '"',
    # Binary number mask (e.g. "1 0 1 1 0 0 1") – not yet in grammar.
    # lambda rng: '"' + " ".join(rng.choice(["0", "1"]) for _ in range(rng.randint(4,16))) + '"',
]


def struct_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply struct/mask mutation to a pattern.

    This implementation works purely at the tree level:

    - It constructs the ``cp_mask_playable`` subtree directly using
      :class:`TreeNode` instances, matching the canonical shape produced
      by parsing expressions such as ``struct ("t f") (s("bd"))`` with
      Lark.
    - The inner pattern is the existing ``PatternTree.root`` (no
      additional prefix transforms or textual round-trips).

    The resulting root has the form::

    control__cp_mask_playable
      STRUCT "struct"
      LPAR "("
      control__pattern_bool__bool_literal
        control__pattern_bool__BOOL "t f ..."
      RPAR ")"
      LPAR "("
      <original-playable-root>
      RPAR ")"
    """
        # 1. Generate mask string (already quoted, e.g. '"t f t f"').
    mask_str = rng.choice(MASK_GENERATORS)(rng)

        # 2. Build the pattern_bool subtree for the mask.
    mask_node = TreeNode(
        op="control__pattern_bool__bool_literal",
        children=[
            TreeNode(op="control__pattern_bool__BOOL", value=mask_str),
        ],
    )

        # 3. Existing tree root is already a playable term, embed it
        # directly as the inner playable.
    inner_playable = tree.root

    # 4. Build the cp_mask_playable root node that wraps the existing
    # pattern.
    new_root = TreeNode(
    op="control__cp_mask_playable",
    children=[
        TreeNode(op="STRUCT", value="struct"),
        TreeNode(op="LPAR", value="("),
        mask_node,
        TreeNode(op="RPAR", value=")"),
        TreeNode(op="LPAR", value="("),
        inner_playable,
        TreeNode(op="RPAR", value=")"),
    ],
    )

    return PatternTree(root=new_root)
