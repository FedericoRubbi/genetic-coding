from __future__ import annotations

"""Stack-based mutation operator.

Wraps an existing playable pattern in a ``stack[...]`` together with a
newly generated playable pattern.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree
from genetic_music.generator.seeds import random_seed_pattern


def stack_wrap(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply stack-based mutation to a pattern.

    This operator wraps the entire existing pattern in a ``stack [...]``
    list, adding a second, randomly generated playable pattern as the new
    sibling. The result is a new pattern tree whose root corresponds to a
    ``stack`` combinator, increasing structural complexity in a
    bottom-up way.
    """
    new_branch_tree = random_seed_pattern(rng)

    # Create the STACK token node
    stack_token = TreeNode(op="STACK", value="stack")

    # Create the cp_list_playable node containing the two patterns
    list_node = TreeNode(
        op="control__cp_list_playable",
        children=[tree.root, new_branch_tree.root],
    )

    # Create the root cp_lists_playable node
    root_node = TreeNode(
        op="control__cp_lists_playable",
        children=[stack_token, list_node],
    )

    return PatternTree(root=root_node)
