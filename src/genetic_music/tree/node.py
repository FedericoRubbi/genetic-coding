"""Base TreeNode class for pattern trees."""

# tidal_gen/tree/node.py
from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class TreeNode:
    op: str
    children: List['TreeNode'] = field(default_factory=list)
    value: Any = None

    def is_leaf(self) -> bool:
        return not self.children
    
    def depth(self) -> int:
        """Calculate tree depth."""
        if self.is_leaf():
            return 1
        return 1 + max(child.depth() for child in self.children)

    def size(self) -> int:
        """Count total nodes in tree."""
        if self.is_leaf():
            return 1
        return 1 + sum(child.size() for child in self.children)

    def __repr__(self) -> str:
        if self.is_leaf():
            return f"{self.op}({self.value})"
        return f"{self.op}({', '.join(repr(c) for c in self.children)})"