"""Base TreeNode class for pattern trees."""

from typing import Any, List, Optional

class TreeNode:
    """Base class for tree nodes in pattern trees."""
    
    def __init__(self, op: str, children: Optional[List['TreeNode']] = None, value: Any = None):
        """
        Args:
            op: Operation name (e.g., 'fast', 'SinOsc', 'LPF')
            children: Child nodes
            value: Leaf value (for terminal nodes)
        """
        self.op = op
        self.children = children or []
        self.value = value
    
    def is_leaf(self) -> bool:
        """Check if this is a terminal node."""
        return len(self.children) == 0
    
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