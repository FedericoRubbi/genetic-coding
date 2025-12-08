from __future__ import annotations

"""Note-based mutation operator.

Creates control patterns using ``n``/``note`` with simple note patterns
and, when needed, adds a sound pattern with ``#`` infix operators.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import NOTE_PATTERN_POOL, SOUND_POOL


NOTE_FUNCTIONS = ["n", "note"]


def note_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply note-based mutation to a pattern."""
    base_branch = tree.root

    # Choose components
    note_func = rng.choice(NOTE_FUNCTIONS)
    note_pattern = rng.choice(NOTE_PATTERN_POOL)
    sound = rng.choice(SOUND_POOL)

    # Detect if base pattern already has sound by checking root op type.
    has_sound = base_branch.op in [
        "control__cp_sound_atom",
        "control__cp_lists_playable",
        "control__cp_euclid_playable",
        "control__cp_mask_playable",
        "control__cp_jux_playable",
        "control__cp_slice_playable",
        "control__cp_chop_playable",
        "control__cp_striate_playable",
        "control__cp_timeops_playable",
        "control__cp_applied_playable",
        "control__cp_playable_term",
        "control_pattern",
    ]

    # 1. Build the note atom: n/note "note_pattern"
    if note_func == "n":
        note_func_token = TreeNode(op="N", value="n")
    else:  # "note"
        note_func_token = TreeNode(op="NOTE", value="note")

    note_atom_node = TreeNode(
        op="control__cp_note_atom",
        children=[
            TreeNode(
                op="control__note_to_cp",
                children=[note_func_token],
            ),
            TreeNode(op="control__STRING", value=f'"{note_pattern}"'),
        ],
    )

    # 2. Build infix operator (OP_HASH)
    hash_op_1 = TreeNode(
        op="control__cp_infix_op",
        children=[TreeNode(op="control__OP_HASH", value="#")],
    )

    if has_sound:
        # Only add note, no additional sound
        new_root = TreeNode(
            op="control_pattern",
            children=[
                base_branch,
                hash_op_1,
                note_atom_node,
            ],
        )
    else:
        # Add both note and sound
        hash_op_2 = TreeNode(
            op="control__cp_infix_op",
            children=[TreeNode(op="control__OP_HASH", value="#")],
        )

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
