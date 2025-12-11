from __future__ import annotations

"""Pattern generation and mutation orchestration.

This module provides the high-level API for generating and mutating
TidalCycles patterns represented as :class:`PatternTree` objects.

Public API:
- ``parse_control_pattern(text)`` -> Lark parse tree
- ``pattern_tree_from_string(text)`` -> :class:`PatternTree`
- ``generate_expressions(n)`` -> list of :class:`PatternTree`
- ``generate_expressions_mutational(n, ...)`` -> list of :class:`PatternTree`
- ``mutate_pattern_tree(tree, ...)`` -> :class:`PatternTree`
"""

import random
from typing import Callable, List, Optional, Sequence

from lark import Tree

from genetic_music.tree.pattern_tree import PatternTree

from .mutations import (
    GROW_MUTATIONS,
    MUTATION_OPERATORS,
    SHRINK_MUTATIONS,
    VALUE_MUTATIONS,
    MutationOp,
)
from .parser import parse_control_pattern
from .seeds import random_seed_pattern


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pattern_tree_from_string(text: str) -> PatternTree:
    """Parse a string and convert it into a :class:`PatternTree`."""

    tree = parse_control_pattern(text)
    return PatternTree.from_lark_tree(tree)


def mutate_pattern_tree(
    tree: PatternTree,
    *,
    mutation_kinds: Optional[Sequence[str]] = None,
    rng: Optional[random.Random] = None,
) -> PatternTree:
    """Apply one of several mutation operators to ``tree`` and return the result.

    Parameters
    ----------
    tree:
        The input :class:`PatternTree` to mutate.
    mutation_kinds:
        A non-empty sequence of mutation operator names to choose from,
        e.g. ``("truncate", "stack_wrap")``. If ``None``, all registered
        operators in :data:`MUTATION_OPERATOR_FACTORIES` are used.
    rng:
        Optional :class:`random.Random` instance to control randomness. If
        omitted, the module-level :mod:`random` is used.

    Returns
    -------
    PatternTree
        A new pattern tree with the mutation applied.

    Raises
    ------
    ValueError
        If an unknown mutation operator name is provided in
        ``mutation_kinds``.
    """
    if rng is None:
        rng = random

    if not mutation_kinds:
        mutation_kinds = list(MUTATION_OPERATORS.keys())

    # Select the mutation operators.
    ops: List[MutationOp] = []
    for name in mutation_kinds:
        op = MUTATION_OPERATORS.get(name)
        if op is None:
            raise ValueError(f"Unknown mutation operator {name!r}")
        ops.append(op)

    selected_op = rng.choice(ops)
    return selected_op(tree, rng)


def generate_expressions(n: int = 10) -> List[PatternTree]:
    """Generate ``n`` random control patterns as :class:`PatternTree` objects.

    This is a convenience wrapper around
    :func:`generate_expressions_mutational` using its default configuration.

    Parameters
    ----------
    n:
        Number of patterns to generate.

    Returns
    -------
    List[PatternTree]
        A list of randomly generated pattern trees.
    """

    return generate_expressions_mutational(n=n)


def generate_expressions_mutational(
    n: int = 10,
    *,
    min_steps: int = 3,
    max_steps: int = 12,
    target_size: Optional[tuple[int, int]] = None,
    target_depth: Optional[tuple[int, int]] = None,
    rng: Optional[random.Random] = None,
) -> List[PatternTree]:
    """Generate ``n`` random patterns by seed-then-mutate over PatternTrees.

    This generator uses a two-phase approach:

      1. Sample a small seed pattern (simple sound/note/stack).
      2. Apply a sequence of tree-level mutation operators to grow and
         enrich the pattern until the desired size/depth region is reached.

    The mutation operators are chosen adaptively based on the current
    tree size and depth: growth operators when the tree is too small,
    shrink operators when too large, and a mix otherwise.

    Parameters
    ----------
    n:
        Number of patterns to generate.
    min_steps, max_steps:
        Range for the number of mutation steps applied to each seed.
    target_size:
        Desired (min, max) range for tree size (node count). Defaults to
        (10, 120).
    target_depth:
        Desired (min, max) range for tree depth. Defaults to (3, 12).
    rng:
        Optional :class:`random.Random` instance to control randomness. If
        omitted, the module-level :mod:`random` is used.

    Returns
    -------
    List[PatternTree]
        A list of randomly generated pattern trees.
    """

    if rng is None:
        rng = random

    if target_size is None:
        target_size = (10, 120)
    if target_depth is None:
        target_depth = (3, 12)

    # Group mutations by their overall effect on structure.
    grow_ops = GROW_MUTATIONS
    value_ops = VALUE_MUTATIONS
    shrink_ops = SHRINK_MUTATIONS

    results: List[PatternTree] = []

    while len(results) < n:
        tree = random_seed_pattern(
            rng if isinstance(rng, random.Random) else random.Random()
        )

        steps = rng.randint(min_steps, max_steps)
        for _ in range(steps):
            size = tree.size()
            depth = tree.depth()

            too_small = size < target_size[0] or depth < target_depth[0]
            too_big = size > target_size[1] or depth > target_depth[1]

            ops: List[MutationOp]

            if too_big and shrink_ops:
                ops = shrink_ops
            elif too_small and grow_ops:
                ops = grow_ops
            else:
                # Within target band: mix growth, value-only tweaks, and
                # occasional shrink.
                p = rng.random()
                if p < 0.5 and grow_ops:
                    ops = grow_ops
                elif p < 0.8 and value_ops:
                    ops = value_ops
                elif shrink_ops:
                    ops = shrink_ops
                else:
                    ops = grow_ops or value_ops or shrink_ops

            if not ops:
                break

            selected_op = rng.choice(ops)

            try:
                tree = selected_op(tree, rng)
            except Exception as e:
                # If a mutation fails for any reason, stop mutating this
                # individual and keep the latest valid tree.
                print(f"Error during mutational generation step: {e}")
                break

        results.append(tree)

    return results
