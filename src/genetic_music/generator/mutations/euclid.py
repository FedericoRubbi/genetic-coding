from __future__ import annotations

"""Euclidean rhythm mutation operator.

Wraps an existing pattern inside a Tidal ``euclid`` expression, with an
optional outer transformation such as ``rev`` or ``fast 2``.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import MutationOp


EUCLID_TRANSFORMS: list[str] = [
    "",        # No transformation
    "rev",     # Reverses the pattern in time
    "fast 2",  # Plays the pattern twice as fast
    "slow 2",  # Plays the pattern at half speed
    "iter 2",  # Iterates pattern twice within the same cycle
]


def euclid_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
) -> MutationOp:
    """Tree-level ``euclid`` mutation operator."""

    # Unused config parameters kept for future tuning.
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Existing playable branch is the current root subtree.
        base_branch = tree.root

        # Choose pulses and steps.
        step_choices = [8, 12, 16, 24, 32]
        steps = rng.choice(step_choices)
        pulses = rng.randint(1, steps)

        # Choose optional outer transformation.
        transform = rng.choice(EUCLID_TRANSFORMS)

        # Build Pattern Int literal nodes for pulses and steps, matching
        # the structure produced by parsing e.g.
        # ``euclid (3) (8) (s("bd"))``.
        pulses_node = TreeNode(
            op="control__pattern_int__int_literal",
            children=[
                TreeNode(op="control__pattern_int__INT", value=str(pulses)),
            ],
        )
        steps_node = TreeNode(
            op="control__pattern_int__int_literal",
            children=[
                TreeNode(op="control__pattern_int__INT", value=str(steps)),
            ],
        )

        # Build the cp_euclid_playable subtree.
        euclid_node = TreeNode(
            op="control__cp_euclid_playable",
            children=[
                TreeNode(op="EUCLID", value="euclid"),
                TreeNode(op="LPAR", value="("),
                pulses_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                steps_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                base_branch,
                TreeNode(op="RPAR", value=")"),
            ],
        )

        # If no transform selected, the euclid node is already a playable term.
        if transform == "":
            return PatternTree(root=euclid_node)

        # Otherwise, wrap the euclid subtree in a prefix_cp-based
        # cp_playable_term.
        if transform == "rev":
            prefix_children = [TreeNode(op="REV", value="rev")]
        elif transform == "fast 2":
            prefix_children = [
                TreeNode(op="FAST", value="fast"),
                TreeNode(op="control__pattern_time__INT", value="2"),
            ]
        elif transform == "slow 2":
            prefix_children = [
                TreeNode(op="SLOW", value="slow"),
                TreeNode(op="control__pattern_time__INT", value="2"),
            ]
        elif transform == "iter 2":
            prefix_children = [
                TreeNode(op="ITER", value="iter"),
                TreeNode(
                    op="control__pattern_int__int_literal",
                    children=[
                        TreeNode(op="control__pattern_int__INT", value="2"),
                    ],
                ),
            ]
        else:
            # Fallback: if an unexpected transform string appears, ignore it.
            return PatternTree(root=euclid_node)

        prefix_node = TreeNode(
            op="control__prefix_cp",
            children=prefix_children,
        )

        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[prefix_node, euclid_node],
        )

        return PatternTree(root=new_root)

    return op
