"""High-level pattern tree built from Lark parse trees.

This module provides the :class:`PatternTree` wrapper, which converts a
`lark.Tree` (or a string parsed by Lark) into a tree of `TreeNode` instances
defined in ``node.py``.  The resulting structure is convenient for genetic
operators and structural analysis (depth, size, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from lark.lexer import Token
from typing import Any, Iterable, Union

from lark import Lark, Tree, Token

from .node import TreeNode

LarkNode = Union[Tree, Token]


def _lark_to_treenode(node: LarkNode) -> TreeNode:
    """Recursively convert a Lark ``Tree``/``Token`` into a ``TreeNode`` tree.

    - Grammar rules (``Tree``) become internal nodes, with ``op`` set to the
      rule name (``Tree.data``) and children converted recursively.
    - Terminals (``Token``) become leaf nodes, with ``op`` set to the token
      type and ``value`` to the token value.
    """
    if isinstance(node, Tree):
        children = [
            _lark_to_treenode(child) for child in node.children if child is not None
        ]
        return TreeNode(op=str(node.data), children=children)

    if isinstance(node, Token):
        return TreeNode(op=str(node.type), value=node.value)

    raise TypeError(f"Unsupported Lark node type: {type(node)!r}")


@dataclass
class PatternTree:
    """Wrapper around a `TreeNode` root with helpers for Lark integration.

    The class is designed so that it behaves like the underlying ``TreeNode``:
    attributes such as ``op``, ``children``, ``value``, and methods like
    ``depth()`` and ``size()`` are transparently forwarded to the root node.
    This keeps existing code that expects a node-like API working.
    """

    root: TreeNode

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_lark_tree(cls, tree: Tree) -> "PatternTree":
        """Build a :class:`PatternTree` from a Lark parse tree."""
        return cls(root=_lark_to_treenode(tree))

    @classmethod
    def from_string(cls, text: str, parser: Lark) -> "PatternTree":
        """Parse ``text`` with the given Lark parser and wrap as ``PatternTree``."""
        lark_tree = parser.parse(text)
        return cls.from_lark_tree(lark_tree)

    # ------------------------------------------------------------------
    # Convenience / proxy methods
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the underlying root ``TreeNode``."""
        return getattr(self.root, name)

    def __repr__(self) -> str:
        return f"PatternTree({repr(self.root)})"

    # Simple iteration helpers, useful for generic traversals
    def iter_nodes(self) -> Iterable[TreeNode]:
        """Depth-first traversal over all nodes in the tree."""

        def _walk(node: TreeNode):
            yield node
            for child in node.children:
                yield from _walk(child)

        return _walk(self.root)

    # ------------------------------------------------------------------
    # Conversion back to a Lark parse tree
    # ------------------------------------------------------------------
    def to_lark_tree(self) -> Tree:
        """Reconstruct the original Lark parse tree from this ``PatternTree``.

        This is essentially the inverse of :func:`_lark_to_treenode`:

        - Internal nodes (with children) become :class:`lark.Tree` instances
          whose ``data`` is the ``TreeNode.op`` and whose children are
          reconstructed recursively.
        - Leaf nodes that have a non-``None`` ``value`` become terminal
          :class:`lark.Token` instances, with ``type`` taken from ``op`` and
          ``value`` preserved as-is.
        - Leaf nodes with ``value is None`` correspond to rule leaves in the
          original parse tree; these are reconstructed as ``Tree`` objects with
          no children (mirroring Lark's behaviour for certain literal-only
          rules such as constructor heads).
        """

        def _to_lark(node: TreeNode) -> LarkNode:
            # Internal nodes: always Trees with recursively converted children.
            if node.children:
                return Tree[Token](
                    node.op, [_to_lark(child) for child in node.children]
                )

            # Leaf with a concrete value: this came from a Token.
            if node.value is not None:
                return Token(node.op, node.value)

            # Leaf without a value: this was a rule leaf in the original tree.
            return Tree[Any](node.op, [])

        return _to_lark(self.root)  # type: ignore[return-value]
