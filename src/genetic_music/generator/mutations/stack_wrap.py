from __future__ import annotations

"""Stack-based mutation operator.

Wraps an existing playable pattern in a ``stack[...]`` together with a
newly generated playable pattern.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import MutationOp


def stack_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a stack-based mutation operator.

    This operator wraps the entire existing pattern in a ``stack [...]``
    list, adding a second, randomly generated playable pattern as the new
    sibling. The result is a new pattern tree whose root corresponds to a
    ``stack`` combinator, increasing structural complexity in a
    bottom-up way.
    """

    # Config knobs are currently unused but kept for a consistent
    # interface and future experimentation (e.g. targeted generation for
    # the new branch).
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Local import to avoid circular imports at module import time.
        from genetic_music.generator.generation import generate_expressions

        new_branch_trees = generate_expressions(1)

        # Create the STACK token node
        stack_token = TreeNode(op="STACK", value="stack")

        # Create the cp_list_playable node containing the two patterns
        list_node = TreeNode(
            op="control__cp_list_playable",
            children=[tree.root, new_branch_trees[0].root],
        )

        # Create the root cp_lists_playable node
        root_node = TreeNode(
            op="control__cp_lists_playable",
            children=[stack_token, list_node],
        )

        return PatternTree(root=root_node)

    return op
