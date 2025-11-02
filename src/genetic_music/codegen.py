"""
Code generation from tree representations to executable code.

Converts PatternTree to TidalCycles code and SynthTree to SuperCollider code.
"""

from typing import Dict
from .genome import PatternTree, SynthTree, TreeNode, TidalGrammar, FunctionType


def to_tidal(tree: PatternTree) -> str:
    """
    Convert a PatternTree to TidalCycles pattern string.
    Uses the grammar system to generate correct syntax for all functions.
    
    Args:
        tree: PatternTree to convert
    
    Returns:
        Tidal pattern code as string
    
    Examples:
        fast(2, sound("bd")) -> "fast 2 $ sound \"bd\""
        stack([sound("bd"), sound("sn")]) -> "stack [sound \"bd\", sound \"sn\"]"
        every(4, rev, sound("bd")) -> "every 4 (rev) $ sound \"bd\""
    """
    # Handle terminal nodes
    if tree.is_leaf():
        if tree.op == 'sound':
            return f'sound "{tree.value}"'
        elif tree.op == 'note':
            return f'note "{tree.value}"'
        elif tree.op == 'silence':
            return 'silence'
        else:
            return str(tree.value)
    
    # Get function signature from grammar (if available)
    func_sig = TidalGrammar.FUNCTIONS.get(tree.op)
    
    if func_sig:
        # Generate code based on function type
        func_type = func_sig.func_type
        
        if func_type == FunctionType.UNARY:
            # Unary: op(pattern)
            child_code = to_tidal(tree.children[0])
            return f"{tree.op} ({child_code})"
        
        elif func_type in [FunctionType.BINARY_NUMERIC, FunctionType.BINARY_INT]:
            # Binary numeric/int: op value $ pattern
            child_code = to_tidal(tree.children[0])
            if func_type == FunctionType.BINARY_INT:
                return f"{tree.op} {int(tree.value)} $ {child_code}"
            else:
                return f"{tree.op} {tree.value:.2f} $ {child_code}"
        
        elif func_type == FunctionType.PROBABILISTIC:
            # Probabilistic: op probability $ pattern
            child_code = to_tidal(tree.children[0])
            return f"{tree.op} {tree.value:.2f} $ {child_code}"
        
        elif func_type == FunctionType.N_ARY:
            # N-ary: op [pattern1, pattern2, ...]
            children_code = [to_tidal(child) for child in tree.children]
            patterns = ', '.join(children_code)
            return f"{tree.op} [{patterns}]"
        
        elif func_type == FunctionType.CONDITIONAL:
            # Conditional: every n (transform) $ pattern
            # or: whenmod n (transform) $ pattern
            if len(tree.children) >= 2:
                transform_code = to_tidal(tree.children[0])
                pattern_code = to_tidal(tree.children[1])
                return f"{tree.op} {int(tree.value)} ({transform_code}) $ {pattern_code}"
            else:
                # Fallback if children are missing
                child_code = to_tidal(tree.children[0])
                return f"{tree.op} {int(tree.value)} $ {child_code}"
    
    # Fallback for unknown operations (shouldn't happen with grammar, but just in case)
    if len(tree.children) == 0:
        return f"{tree.op}"
    elif len(tree.children) == 1:
        child_code = to_tidal(tree.children[0])
        if tree.value is not None:
            return f"{tree.op} {tree.value} $ {child_code}"
        else:
            return f"{tree.op} ({child_code})"
    else:
        children_code = [to_tidal(child) for child in tree.children]
        return f"{tree.op} [{', '.join(children_code)}]"
