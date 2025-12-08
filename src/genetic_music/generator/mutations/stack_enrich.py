from __future__ import annotations

"""Stack-enrichment mutation operator.

Enriches existing ``stack``/``cat``-style list combinators by appending
additional randomly generated branches.
"""

import random

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree
from genetic_music.generator.seeds import random_seed_pattern

from .common import clone_treenode


def _collect_stack_nodes(root: TreeNode) -> list[tuple[TreeNode, TreeNode]]:
    """Return ``(lists_node, list_node)`` pairs for all ``cp_lists_playable`` nodes."""
    nodes: list[tuple[TreeNode, TreeNode]] = []

    def _walk(node: TreeNode) -> None:
        if node.op == "control__cp_lists_playable" and len(node.children) >= 2:
            list_node = node.children[1]
            if list_node.op == "control__cp_list_playable":
                nodes.append((node, list_node))
        for child in node.children:
            _walk(child)

    _walk(root)
    return nodes


def _enrich_once(root: TreeNode, rng: random.Random) -> TreeNode:
    candidates = _collect_stack_nodes(root)
    if not candidates:
        return root

    _, list_node = rng.choice(candidates)

    # Decide how many new branches to add
    n_new = rng.randint(1, 3)
    new_branch_trees = [random_seed_pattern(rng) for _ in range(n_new)]

    for pt in new_branch_trees:
        # Append the playable subtree root directly to the list
        list_node.children.append(pt.root)

    return root


def stack_enrich(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply stack-enrichment mutation to a pattern."""
    # Operate on a clone to avoid mutating the input tree
    new_root = clone_treenode(tree.root)
    new_root = _enrich_once(new_root, rng)
    return PatternTree(root=new_root)
