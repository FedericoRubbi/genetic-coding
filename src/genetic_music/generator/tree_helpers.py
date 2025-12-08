from __future__ import annotations

"""Tree traversal and manipulation helpers.

These utilities are used by crossover operations and some tree-level
mutations that need to navigate or modify specific nodes within a tree
structure.
"""

from typing import List, Optional

from genetic_music.tree.node import TreeNode


def iter_nodes_with_paths(
    root: TreeNode, path_prefix: Optional[List[int]] = None
) -> List[tuple[List[int], TreeNode]]:
    """Return a list of ``(path, node)`` pairs for all nodes in the tree.

    ``path`` is a list of child indices from the root to the node.
    """

    if path_prefix is None:
        path_prefix = []

    results: List[tuple[List[int], TreeNode]] = []

    def _walk(node: TreeNode, path: List[int]) -> None:
        results.append((path, node))
        for idx, child in enumerate(node.children):
            _walk(child, path + [idx])

    _walk(root, path_prefix)
    return results


def clone_with_replacement(
    node: TreeNode, path: List[int], new_subtree: TreeNode
) -> TreeNode:
    """Clone ``node`` while replacing the node at ``path`` with ``new_subtree``."""

    if not path:
        # We are at the target node; replace entirely.
        return new_subtree

    idx = path[0]
    # Clone current node with potentially replaced child.
    new_children: List[TreeNode] = []
    for i, child in enumerate(node.children):
        if i == idx:
            new_children.append(clone_with_replacement(child, path[1:], new_subtree))
        else:
            # Shallow copy of unaffected children is fine; they are
            # immutable for our purposes.
            new_children.append(child)

    return TreeNode(op=node.op, children=new_children, value=node.value)
