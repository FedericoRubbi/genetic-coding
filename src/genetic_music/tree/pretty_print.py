"""Utility functions for pretty-printing tree structures.

This module provides functions to visualize TreeNode and PatternTree objects
in a human-readable, hierarchical format using box-drawing characters.
"""

from typing import List
from .node import TreeNode
from .pattern_tree import PatternTree


def pretty_print(tree, show_types: bool = True, compact: bool = False) -> str:
    """Pretty print a tree structure with visual hierarchy.
    
    Args:
        tree: Either a TreeNode or PatternTree instance to visualize
        show_types: If True, show the operation/rule names (default: True)
        compact: If True, use a more compact representation (default: False)
        
    Returns:
        A string with the formatted tree representation
        
    Example:
        >>> tree = TreeNode(op="pattern", children=[
        ...     TreeNode(op="note", value="c"),
        ...     TreeNode(op="note", value="e")
        ... ])
        >>> print(pretty_print(tree))
        pattern
        ├── note: c
        └── note: e
    """
    # Handle PatternTree wrapper
    if isinstance(tree, PatternTree):
        tree = tree.root
    
    if not isinstance(tree, TreeNode):
        raise TypeError(f"Expected TreeNode or PatternTree, got {type(tree)}")
    
    lines: List[str] = []
    _build_tree_lines(tree, lines, "", True, show_types, compact, is_root=True)
    return "\n".join(lines)


def _build_tree_lines(
    node: TreeNode,
    lines: List[str],
    prefix: str,
    is_last: bool,
    show_types: bool,
    compact: bool,
    is_root: bool = False
) -> None:
    """Recursively build the lines for tree visualization.
    
    Args:
        node: Current node to process
        lines: List to accumulate output lines
        prefix: Prefix for the current line (for indentation)
        is_last: Whether this node is the last child of its parent
        show_types: Whether to show operation/rule names
        compact: Whether to use compact formatting
        is_root: Whether this is the root node
    """
    # Choose the branch characters
    if is_root:
        # Root node gets no branch characters
        branch = ""
    else:
        branch = "└── " if is_last else "├── "
    
    # Format the node content
    content = _format_node_content(node, show_types, compact)
    
    # Add the current node's line
    lines.append(f"{prefix}{branch}{content}")
    
    # Prepare prefix for children
    if node.children:
        if is_root:
            # Root node's children start with no prefix
            child_prefix = ""
        else:
            # Add vertical line or spaces depending on whether parent is last child
            child_prefix = prefix + ("    " if is_last else "│   ")
    
    # Recursively add children
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        _build_tree_lines(child, lines, child_prefix, is_last_child, show_types, compact, is_root=False)


def _format_node_content(node: TreeNode, show_types: bool, compact: bool) -> str:
    """Format the content of a single node.
    
    Args:
        node: The node to format
        show_types: Whether to show the operation type
        compact: Whether to use compact formatting
        
    Returns:
        Formatted string for the node
    """
    if node.is_leaf():
        # Leaf node with a value
        if node.value is not None:
            if show_types:
                if compact:
                    return f"{node.op}:{node.value}"
                else:
                    return f"{node.op}: {node.value}"
            else:
                return str(node.value)
        # Leaf node without a value (rule leaf)
        else:
            return f"{node.op}" if show_types else "(empty)"
    else:
        # Internal node
        child_count = len(node.children)
        if show_types:
            # Build the base string with op and child count
            if compact:
                base = f"{node.op}[{child_count}]"
            else:
                base = f"{node.op} ({child_count} children)"
            
            # Add value if present
            if node.value is not None:
                if compact:
                    return f"{base}:{node.value}"
                else:
                    return f"{base} = {node.value}"
            else:
                return base
        else:
            # Without types, show value if present
            if node.value is not None:
                return f"({child_count} children) = {node.value}"
            else:
                return f"({child_count} children)"


def print_tree(tree, show_types: bool = True, compact: bool = False) -> None:
    """Print a tree to stdout with visual hierarchy.
    
    This is a convenience function that calls pretty_print() and prints the result.
    
    Args:
        tree: Either a TreeNode or PatternTree instance to visualize
        show_types: If True, show the operation/rule names (default: True)
        compact: If True, use a more compact representation (default: False)
    """
    print(pretty_print(tree, show_types, compact))


def tree_summary(tree) -> str:
    """Get a summary of tree statistics.
    
    Args:
        tree: Either a TreeNode or PatternTree instance
        
    Returns:
        A string with tree statistics (depth, size, leaf count)
    """
    # Handle PatternTree wrapper
    if isinstance(tree, PatternTree):
        tree = tree.root
    
    if not isinstance(tree, TreeNode):
        raise TypeError(f"Expected TreeNode or PatternTree, got {type(tree)}")
    
    depth = tree.depth()
    size = tree.size()
    leaf_count = _count_leaves(tree)
    internal_count = size - leaf_count
    
    return (
        f"Tree Summary:\n"
        f"  Depth: {depth}\n"
        f"  Total nodes: {size}\n"
        f"  Leaf nodes: {leaf_count}\n"
        f"  Internal nodes: {internal_count}"
    )


def _count_leaves(node: TreeNode) -> int:
    """Count the number of leaf nodes in a tree."""
    if node.is_leaf():
        return 1
    return sum(_count_leaves(child) for child in node.children)


def print_tree_with_summary(tree, show_types: bool = True, compact: bool = False) -> None:
    """Print a tree with its summary statistics.
    
    Args:
        tree: Either a TreeNode or PatternTree instance to visualize
        show_types: If True, show the operation/rule names (default: True)
        compact: If True, use a more compact representation (default: False)
    """
    print(tree_summary(tree))
    print()
    print_tree(tree, show_types, compact)

