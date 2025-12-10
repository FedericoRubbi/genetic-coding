from __future__ import annotations

"""Scale-based mutation operator.

Enriches a pattern with a scale-based note pattern and a sound using
``#`` infix combinators.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import (
    SCALE_INT_PATTERN_GENERATOR,
    SCALE_NAME_POOL,
    SOUND_POOL,
)


def scale_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply scale-based mutation to a pattern.

    Constructs patterns like::

    basePattern # n(scale "major" "0") # s("bd")

    The tree structure follows the left-associative infix chain::

    control_pattern
      <base_playable>
      control__cp_infix_op (OP_HASH)
      control__cp_note_atom (n(scale ...))
      control__cp_infix_op (OP_HASH)
      control__cp_sound_atom (s(...))
    """
    base_branch = tree.root
    scale_name = rng.choice(SCALE_NAME_POOL)
    int_pattern = SCALE_INT_PATTERN_GENERATOR(rng)
    sound = rng.choice(SOUND_POOL)

        # 1. Build the scale constructor: n(scale "scale_name" "int_pattern")
    scale_literal_node = TreeNode(
        op="control__pattern_note__pattern_string_scale__scale_literal",
        children=[
            TreeNode(
                op="control__pattern_note__pattern_string_scale__SCALE_STRING",
                value=f'"{scale_name}"',
            )
        ],
    )

    int_string_literal_node = TreeNode(
        op="control__pattern_note__pattern_int__int_string_literal",
        children=[
            TreeNode(
                op="control__pattern_note__pattern_int__STRING",
                value=f'"{int_pattern}"',
            )
        ],
    )

    scale_ctor_node = TreeNode(
        op="control__pattern_note__scale_ctor",
        children=[scale_literal_node, int_string_literal_node],
    )

    note_atom_node = TreeNode(
        op="control__cp_note_atom",
        children=[
            TreeNode(
                op="control__note_to_cp",
                children=[TreeNode(op="N", value="n")],
            ),
            scale_ctor_node,
        ],
    )

        # 2. Build the sound atom: s("sound")
    sound_atom_node = TreeNode(
        op="control__cp_sound_atom",
        children=[
            TreeNode(op="S", value="s"),
            TreeNode(op="LPAR", value="("),
            TreeNode(
                op="control__pattern_string_sample__sample_literal",
                children=[
                    TreeNode(
                        op="control__pattern_string_sample__SAMPLE_STRING",
                        value=f'"{sound}"',
                    )
                ],
            ),
            TreeNode(op="RPAR", value=")"),
        ],
    )

        # 3. Build infix operators (OP_HASH)
    hash_op_1 = TreeNode(
        op="control__cp_infix_op",
        children=[TreeNode(op="control__OP_HASH", value="#")],
    )

    hash_op_2 = TreeNode(
        op="control__cp_infix_op",
        children=[TreeNode(op="control__OP_HASH", value="#")],
    )

    # 4. Build the control_pattern root with left-associative infix chain
    new_root = TreeNode(
    op="control_pattern",
    children=[
        base_branch,
        hash_op_1,
        note_atom_node,
        hash_op_2,
        sound_atom_node,
    ],
    )

    return PatternTree(root=new_root)
