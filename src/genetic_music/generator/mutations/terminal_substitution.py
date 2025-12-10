from __future__ import annotations

"""Terminal-substitution mutation operator.

Randomly substitutes terminal musical values (sounds, note patterns,
scale names and degree patterns) while preserving tree structure.
"""

import random
from typing import Any

from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

from .common import (
    NOTE_PATTERN_GENERATOR,
    SCALE_INT_PATTERN_GENERATOR,
    SCALE_NAME_POOL,
    SOUND_POOL,
    clone_treenode,
)


def terminal_substitution(tree: PatternTree, rng: random.Random) -> PatternTree:
    """Randomly substitute terminal musical values in-place."""
    # Per-node mutation probabilities
    SOUND_PROB = 0.5
    NOTE_PROB = 0.5
    SCALE_PROB = 0.5

    def _choose_new_quoted(current: Any, pool: list[str], rng: random.Random) -> str:
        if not isinstance(current, str):
            inner_current = None
        elif len(current) >= 2 and current[0] == '"' and current[-1] == '"':
            inner_current = current[1:-1]
        else:
            inner_current = current

        if len(pool) > 1 and inner_current in pool:
            choices = [v for v in pool if v != inner_current]
        else:
            choices = pool

        new_inner = rng.choice(choices)
        return f'"{new_inner}"'

    def _maybe_substitute(node: TreeNode, rng: random.Random) -> None:
        op = node.op

        # Sounds: control__pattern_string_sample__SAMPLE_STRING
        if op == "control__pattern_string_sample__SAMPLE_STRING":
            if rng.random() < SOUND_PROB:
                node.value = _choose_new_quoted(node.value, SOUND_POOL, rng)
            return

        # Note patterns: control__STRING (used under cp_note_atom)
        if op == "control__STRING":
            if rng.random() < NOTE_PROB:
                # Generate a fresh single-octave note pattern string.
                new_pattern = NOTE_PATTERN_GENERATOR(rng)
                node.value = f'"{new_pattern}"'
            return

        # Scale names: control__pattern_note__pattern_string_scale__SCALE_STRING
        if op == "control__pattern_note__pattern_string_scale__SCALE_STRING":
            if rng.random() < SCALE_PROB:
                node.value = _choose_new_quoted(node.value, SCALE_NAME_POOL, rng)
            return

        # Scale degree patterns: control__pattern_note__pattern_int__STRING
        if op == "control__pattern_note__pattern_int__STRING":
            if rng.random() < SCALE_PROB:
                # Generate a fresh scale-degree pattern string.
                new_pattern = SCALE_INT_PATTERN_GENERATOR(rng)
                node.value = f'"{new_pattern}"'
            return

    def _walk(node: TreeNode) -> None:
        _maybe_substitute(node, rng)
        for child in node.children:
            _walk(child)

    # Work on a cloned tree to avoid mutating the input in-place
    new_root = clone_treenode(tree.root)
    _walk(new_root)
    return PatternTree(root=new_root)
