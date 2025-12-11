from __future__ import annotations

"""Truncation mutation operator.

Simplifies composite patterns by truncating overlay/append/stack-style
combinators.
"""

import random
from typing import Optional

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import clone_treenode


# Token types for named binary combinators we want to truncate.
BINARY_HEAD_TOKENS = {
    "OVERLAY",
    "APPEND",
    "SLOWAPPEND",
    "FASTAPPEND",
    "INTERLACE",
}

# Ops that correspond to playable CP roots (from cp_playable_term alternatives).
PLAYABLE_OPS = {
    "control__cp_playable_term",
    "control__cp_sound_atom",
    "control__cp_note_atom",
    "control__cp_applied_playable",
    "control__cp_jux_playable",
    "control__cp_slice_playable",
    "control__cp_chop_playable",
    "control__cp_mask_playable",
    "control__cp_striate_playable",
    "control__cp_euclid_playable",
    "control__cp_timeops_playable",
    "control__cp_lists_playable",
}


def _collect_candidates(
    root: TreeNode,
) -> list[tuple[str, TreeNode, Optional[TreeNode], Optional[int]]]:
    candidates: list[tuple[str, TreeNode, Optional[TreeNode], Optional[int]]] = []

    def _walk(
        node: TreeNode, parent: Optional[TreeNode], index_in_parent: Optional[int]
    ) -> None:
        # Binary named combinators under cp_playable_term
        if node.op == "control__cp_playable_term" and len(node.children) >= 3:
            head = node.children[0]
            if head.op == "control__cp_binary_named" and head.children:
                head_tok = head.children[0]
                if head_tok.op in BINARY_HEAD_TOKENS:
                    candidates.append(("binary", node, parent, index_in_parent))

        # Stack/list combinators: cp_lists_playable(stack/cat/... [ ... ])
        if node.op == "control__cp_lists_playable" and len(node.children) >= 2:
            list_node = node.children[1]
            if list_node.op == "control__cp_list_playable" and list_node.children:
                candidates.append(("list", node, parent, index_in_parent))

        for idx, child in enumerate(node.children):
            _walk(child, node, idx)

    _walk(root, None, None)
    return candidates


def _truncate_once(root: TreeNode, rng: random.Random) -> TreeNode:
    candidates = _collect_candidates(root)
    if not candidates:
        return root

    kind, node, parent, index_in_parent = rng.choice(candidates)

    # Decide which subtree should replace the combinator node
    survivor: Optional[TreeNode] = None

    if kind == "binary":
        # Expect shape: [binary_head, left, right, ...]
        if len(node.children) >= 3:
            left = node.children[1]
            right = node.children[2]
            survivor = left if rng.random() < 0.5 else right

    elif kind == "list":
        # Expect shape: [STACK/CAT token, cp_list_playable]
        list_node = node.children[1]
        # Filter to playable children only, to preserve cp_playable_term invariants
        playable_children = [c for c in list_node.children if c.op in PLAYABLE_OPS]
        if playable_children:
            survivor = rng.choice(playable_children)

    # If something unexpected happened, leave the tree unchanged
    if survivor is None:
        return root

    # Replace in parent or at root
    if parent is None or index_in_parent is None:
        # Truncated node was the root
        return survivor

    parent.children[index_in_parent] = survivor
    return root


def truncate(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Apply truncation mutation to a pattern."""
    # Operate on a clone to avoid mutating the input tree
    new_root = clone_treenode(tree.root)
    new_root = _truncate_once(new_root, rng)
    return PatternTree(root=new_root)
