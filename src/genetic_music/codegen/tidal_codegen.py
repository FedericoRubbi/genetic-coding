"""Tree -> Tidal code generator for `PatternTree`.

For now this generator reconstructs the original token stream by walking the
`PatternTree` and rejoining all leaf values with a simple spacing heuristic.
Because `PatternTree` is built directly from the Lark parse tree over the
Tidal grammar, this already yields valid Tidal source for any parsed pattern.
"""

from __future__ import annotations

from typing import List

from lark import Lark
from lark.reconstruct import Reconstructor

from genetic_music.tree.pattern_tree import PatternTree

# Build a dedicated parser instance for reconstruction. We deliberately disable
# ``maybe_placeholders`` so that Lark's :class:`Reconstructor` can operate on
# the grammar (it asserts this option is ``False``).
_RECON_PARSER: Lark = Lark.open(
    "src/genetic_music/grammar/main.lark",
    start="control_pattern",
    maybe_placeholders=False,
)
_RECONSTRUCTOR: Reconstructor = Reconstructor(_RECON_PARSER)


def to_tidal(tree: PatternTree) -> str:
    """Convert a `PatternTree` into a Tidal pattern string.

    This implementation is grammar-aware and proceeds in two steps:

    1. Reconstruct the original Lark parse tree via
       :meth:`PatternTree.to_lark_tree`, which inverts the internal
       ``TreeNode`` representation back into a :class:`lark.Tree`.
    2. Use Lark's :class:`Reconstructor` (built from the Earley parser) to
       generate a textual ``control_pattern`` expression that is guaranteed to
       be accepted by the same grammar and to preserve the original structure.
    """
    lark_tree = tree.to_lark_tree()
    return _RECONSTRUCTOR.reconstruct(lark_tree)


