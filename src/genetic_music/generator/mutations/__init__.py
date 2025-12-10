from __future__ import annotations

"""Mutation operator package.

This package contains one module per tree-level mutation operator plus a
small registry that groups them by structural effect.
"""

from typing import Mapping

from .append import append_pattern
from .common import MutationOp
from .euclid import euclid_wrap
from .note_wrap import note_wrap
from .overlay_wrap import overlay_wrap
from .scale_wrap import scale_wrap
from .speed import speed_change
from .stack_enrich import stack_enrich
from .stack_wrap import stack_wrap
from .striate import striate_wrap
from .struct import struct_wrap
from .terminal_substitution import terminal_substitution
from .truncate import truncate

# Operators exposed (by name) to :func:`mutate_pattern_tree`.
#
# Only "truncate" is enabled by default to preserve prior behaviour; add
# more entries here to make additional operators available by name.
MUTATION_OPERATORS: Mapping[str, MutationOp] = {
    "stack_wrap": stack_wrap,
    "overlay_wrap": overlay_wrap,
    "append_pattern": append_pattern,
    "scale_wrap": scale_wrap,
    "note_wrap": note_wrap,
    "euclid_wrap": euclid_wrap,
    "struct_wrap": struct_wrap,
    "striate_wrap": striate_wrap,
    "speed_change": speed_change,
    "stack_enrich": stack_enrich,
    "terminal_substitution": terminal_substitution,
    "truncate": truncate,
}

# Groupings used by :func:`generate_expressions_mutational` to bias the
# choice of mutation operators depending on the current tree size/depth.
GROW_MUTATIONS: list[MutationOp] = [
    stack_wrap,
    overlay_wrap,
    append_pattern,
    scale_wrap,
    note_wrap,
    euclid_wrap,
    struct_wrap,
    striate_wrap,
    speed_change,
    stack_enrich,
]

VALUE_MUTATIONS: list[MutationOp] = [
    terminal_substitution,
]

SHRINK_MUTATIONS: list[MutationOp] = [
    truncate,
]
