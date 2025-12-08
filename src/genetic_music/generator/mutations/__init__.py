from __future__ import annotations

"""Mutation operator package.

This package contains one module per tree-level mutation operator plus a
small registry that groups them by structural effect.
"""

from typing import Callable, Mapping

from .append import append_op_factory
from .common import MutationOp
from .euclid import euclid_op_factory
from .note_wrap import note_wrap_op_factory
from .overlay_wrap import overlay_wrap_op_factory
from .scale_wrap import scale_wrap_op_factory
from .speed import speed_op_factory
from .stack_enrich import stack_enrich_op_factory
from .stack_wrap import stack_wrap_op_factory
from .striate import striate_op_factory
from .struct import struct_op_factory
from .terminal_substitution import terminal_substitution_op_factory
from .truncate import truncate_op_factory

# Operators exposed (by name) to :func:`mutate_pattern_tree`.
#
# Only "truncate" is enabled by default to preserve prior behaviour; add
# more entries here to make additional operators available by name.
MUTATION_OPERATOR_FACTORIES: Mapping[str, Callable[..., MutationOp]] = {
    "truncate": truncate_op_factory,
}

# Groupings used by :func:`generate_expressions_mutational` to bias the
# choice of mutation operators depending on the current tree size/depth.
GROW_MUTATION_FACTORIES: list[Callable[..., MutationOp]] = [
    stack_wrap_op_factory,
    overlay_wrap_op_factory,
    append_op_factory,
    scale_wrap_op_factory,
    note_wrap_op_factory,
    euclid_op_factory,
    struct_op_factory,
    striate_op_factory,
    speed_op_factory,
    stack_enrich_op_factory,
]

VALUE_MUTATION_FACTORIES: list[Callable[..., MutationOp]] = [
    terminal_substitution_op_factory,
]

SHRINK_MUTATION_FACTORIES: list[Callable[..., MutationOp]] = [
    truncate_op_factory,
]
