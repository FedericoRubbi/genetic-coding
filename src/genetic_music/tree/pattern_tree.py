"""PatternTree implementation for TidalCycles."""

import random
from typing import List
from .node import TreeNode
from ..grammar.tidal_grammar import TidalGrammar
from ..grammar.function_type import FunctionType

class PatternTree(TreeNode):
    """
    Tree representation of TidalCycles patterns.
    Uses TidalGrammar for function signatures and generation.
    """
    
    # Terminal types
    TERMINALS = ['sound', 'note', 'silence']
    
    @classmethod
    def random(cls, max_depth: int = 4, method: str = 'grow') -> 'PatternTree':
        """
        Generate a random pattern tree using the grammar.
        
        Args:
            max_depth: Maximum tree depth
            method: 'grow' (variable depth) or 'full' (fixed depth)
        
        Returns:
            Random PatternTree
        """
        # Terminal probability based on method and depth
        terminal_prob = 0.3 if method == 'grow' else 0.0
        
        if max_depth <= 1 or (method == 'grow' and random.random() < terminal_prob):
            # Create terminal node
            return cls._generate_terminal()
        
        # Create non-terminal node using grammar
        return cls._generate_nonterminal(max_depth, method)
    
    @classmethod
    def _generate_terminal(cls) -> 'PatternTree':
        """Generate a terminal (leaf) node."""
        terminal = random.choice(cls.TERMINALS)
        
        if terminal == 'sound':
            value = random.choice(TidalGrammar.SOUNDS)
        elif terminal == 'note':
            value = random.randint(0, 11)  # MIDI note (octave)
        else:  # silence
            value = None
        
        return cls(terminal, [], value)
    
    @classmethod
    def _generate_nonterminal(cls, max_depth: int, method: str) -> 'PatternTree':
        """Generate a non-terminal node using the grammar."""
        # Select a random function signature
        func_sig = random.choice(TidalGrammar.get_all_functions())
        
        # Generate parameter (if needed)
        param = func_sig.generate_param()
        
        # Generate children based on signature type
        children = []
        
        if func_sig.func_type == FunctionType.UNARY:
            # Single pattern child
            child = cls.random(max_depth - 1, method)
            children = [child]
        
        elif func_sig.func_type in [FunctionType.BINARY_NUMERIC, 
                                     FunctionType.BINARY_INT,
                                     FunctionType.PROBABILISTIC]:
            # Numeric/int parameter + single pattern child
            child = cls.random(max_depth - 1, method)
            children = [child]
        
        elif func_sig.func_type == FunctionType.N_ARY:
            # Multiple pattern children
            num_children = func_sig.get_num_children()
            children = [cls.random(max_depth - 1, method) for _ in range(num_children)]
        
        elif func_sig.func_type == FunctionType.CONDITIONAL:
            # Conditional: (n, transform_pattern, base_pattern)
            # Generate two children - transform and base pattern
            transform = cls.random(max_depth - 1, 'grow')
            pattern = cls.random(max_depth - 1, method)
            children = [transform, pattern]
        
        return cls(func_sig.name, children, param)