from __future__ import annotations

"""Pattern generation and mutation for TidalCycles.

This package provides utilities for generating, parsing, and mutating
TidalCycles patterns represented as :class:`PatternTree` objects.

Public API
----------
From :mod:`.generation`:
    - :func:`parse_control_pattern` - Parse text to Lark tree
    - :func:`pattern_tree_from_string` - Parse text to PatternTree
    - :func:`generate_expressions` - Generate random patterns
    - :func:`generate_expressions_mutational` - Generate with mutation control
    - :func:`mutate_pattern_tree` - Apply mutations to a pattern

From :mod:`.tree_helpers`:
    - :func:`iter_nodes_with_paths` - Tree traversal with paths
    - :func:`clone_with_replacement` - Clone tree with node replacement

From :mod:`.mutations`:
    - :data:`MUTATION_OPERATOR_FACTORIES` - Registry of available mutations
    - :data:`GROW_MUTATION_FACTORIES` - Growth-oriented mutations
    - :data:`VALUE_MUTATION_FACTORIES` - Value-substitution mutations
    - :data:`SHRINK_MUTATION_FACTORIES` - Simplification mutations
"""

from .generation import (
    generate_expressions,
    generate_expressions_mutational,
    mutate_pattern_tree,
    parse_control_pattern,
    pattern_tree_from_string,
)
from .mutations import (
    GROW_MUTATIONS,
    MUTATION_OPERATORS,
    SHRINK_MUTATIONS,
    VALUE_MUTATIONS,
)
from .tree_helpers import clone_with_replacement, iter_nodes_with_paths

__all__ = [
    # Pattern generation and parsing
    "generate_expressions",
    "generate_expressions_mutational",
    "parse_control_pattern",
    "pattern_tree_from_string",
    # Mutation
    "mutate_pattern_tree",
    "MUTATION_OPERATORS",
    "GROW_MUTATIONS",
    "VALUE_MUTATIONS",
    "SHRINK_MUTATIONS",
    # Tree helpers
    "iter_nodes_with_paths",
    "clone_with_replacement",
]
