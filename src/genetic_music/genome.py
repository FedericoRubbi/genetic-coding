"""
Genome representation for musical patterns and synthesis.

This module defines the genetic representation of musical individuals as pattern trees (TidalCycles).
"""

import random
from typing import List, Any, Optional, Dict, Callable
from dataclasses import dataclass
from enum import Enum


class FunctionType(Enum):
    """Types of TidalCycles function signatures."""
    UNARY = "unary"  # (pattern) -> pattern
    BINARY_NUMERIC = "binary_numeric"  # (number, pattern) -> pattern
    BINARY_INT = "binary_int"  # (int, pattern) -> pattern
    N_ARY = "n_ary"  # (pattern, pattern, ...) -> pattern
    CONDITIONAL = "conditional"  # (int, pattern, pattern) -> pattern
    PROBABILISTIC = "probabilistic"  # (float[0-1], pattern) -> pattern


@dataclass
class FunctionSignature:
    """
    Defines the signature and parameter generation for a TidalCycles function.
    
    Attributes:
        name: Function name
        func_type: Type of function signature
        param_generator: Optional function to generate numeric/int parameters
        min_children: Minimum number of pattern children
        max_children: Maximum number of pattern children
    """
    name: str
    func_type: FunctionType
    param_generator: Optional[Callable[[], Any]] = None
    min_children: int = 1
    max_children: int = 1
    
    def generate_param(self) -> Any:
        """Generate a parameter value if needed."""
        if self.param_generator:
            return self.param_generator()
        return None
    
    def get_num_children(self) -> int:
        """Get number of children to generate."""
        if self.min_children == self.max_children:
            return self.min_children
        return random.randint(self.min_children, self.max_children)


class TidalGrammar:
    """
    Grammar definition for TidalCycles pattern functions.
    Defines available functions and their signatures.
    """
    
    # Terminal sound samples (SuperDirt defaults)
    SOUNDS = [
        # Drums
        'bd', 'sn', 'cp', 'hh', 'oh', 'ch', 'cy', 'rim', 'tom',
        # Percussion
        'clap', 'click', 'cowbell', 'crash', 'hand', 'tabla',
        # Bass & Tonal
        'arpy', 'bass', 'bass0', 'bass1', 'bass2', 'bass3',
        # Synths
        'superpiano', 'supersaw', 'supermandolin', 'supersquare',
        # Breaks & Loops
        'breaks125', 'breaks152', 'breaks165', 'amencutup',
        # Industrial
        'industrial', 'insect', 'jazz', 'jungbass',
        # 808/909
        '808bd', '808sd', '808hh', '808oh', '808cy'
    ]
    
    # Function signatures organized by type
    FUNCTIONS: Dict[str, FunctionSignature] = {
        # === UNARY TRANSFORMERS (pattern -> pattern) ===
        'rev': FunctionSignature('rev', FunctionType.UNARY),
        'palindrome': FunctionSignature('palindrome', FunctionType.UNARY),
        'brak': FunctionSignature('brak', FunctionType.UNARY),
        'degrade': FunctionSignature('degrade', FunctionType.UNARY),
        'shuffle': FunctionSignature('shuffle', FunctionType.UNARY),
        'scramble': FunctionSignature('scramble', FunctionType.UNARY),
        
        # === BINARY NUMERIC (number, pattern -> pattern) ===
        'fast': FunctionSignature(
            'fast', 
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'slow': FunctionSignature(
            'slow',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'density': FunctionSignature(
            'density',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'sparsity': FunctionSignature(
            'sparsity',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'hurry': FunctionSignature(
            'hurry',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 2.0)
        ),
        'ply': FunctionSignature(
            'ply',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 4)
        ),
        'iter': FunctionSignature(
            'iter',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 8)
        ),
        'chop': FunctionSignature(
            'chop',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 16)
        ),
        'striate': FunctionSignature(
            'striate',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 16)
        ),
        
        # === PROBABILISTIC (float, pattern -> pattern) ===
        'degradeBy': FunctionSignature(
            'degradeBy',
            FunctionType.PROBABILISTIC,
            param_generator=lambda: random.uniform(0.1, 0.7)
        ),
        'sometimesBy': FunctionSignature(
            'sometimesBy',
            FunctionType.PROBABILISTIC,
            param_generator=lambda: random.uniform(0.2, 0.8)
        ),
        
        # === N-ARY COMBINATORS (multiple patterns) ===
        'stack': FunctionSignature(
            'stack',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'cat': FunctionSignature(
            'cat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'fastcat': FunctionSignature(
            'fastcat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'slowcat': FunctionSignature(
            'slowcat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'append': FunctionSignature(
            'append',
            FunctionType.N_ARY,
            min_children=2,
            max_children=2
        ),
        'overlay': FunctionSignature(
            'overlay',
            FunctionType.N_ARY,
            min_children=2,
            max_children=3
        ),
        
        # === CONDITIONAL (int, pattern, pattern -> pattern) ===
        'every': FunctionSignature(
            'every',
            FunctionType.CONDITIONAL,
            param_generator=lambda: random.randint(2, 8),
            min_children=2,
            max_children=2
        ),
        'whenmod': FunctionSignature(
            'whenmod',
            FunctionType.CONDITIONAL,
            param_generator=lambda: random.randint(3, 8),
            min_children=2,
            max_children=2
        ),
    }
    
    # Get lists of functions by type for easier selection
    @classmethod
    def get_functions_by_type(cls, func_type: FunctionType) -> List[FunctionSignature]:
        """Get all functions of a specific type."""
        return [sig for sig in cls.FUNCTIONS.values() if sig.func_type == func_type]
    
    @classmethod
    def get_all_functions(cls) -> List[FunctionSignature]:
        """Get all function signatures."""
        return list(cls.FUNCTIONS.values())


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


@dataclass
class Genome:
    """
    Complete genome containing pattern trees.
    """
    pattern_tree: PatternTree
    fitness: float = 0.0
    
    @classmethod
    def random(cls, pattern_depth: int = 4) -> 'Genome':
        """Create a random genome."""
        return cls(
            pattern_tree=PatternTree.random(pattern_depth)
        )
    
    def mutate(self, rate: float = 0.1) -> 'Genome':
        """
        Mutate the genome.
        
        Args:
            rate: Mutation probability
        
        Returns:
            Mutated genome (new instance)
        """
        if random.random() > rate:
            return self
        
        def get_paths(node: TreeNode, current_path: Optional[List[int]] = None) -> List[List[int]]:
            path = current_path or []
            paths = [path]
            for idx, child in enumerate(node.children):
                paths.extend(get_paths(child, path + [idx]))
            return paths
        
        def replace_at_path(node: TreeNode, path: List[int], new_subtree: TreeNode) -> TreeNode:
            if not path:
                return new_subtree
            idx = path[0]
            new_children = list(node.children)
            new_children[idx] = replace_at_path(new_children[idx], path[1:], new_subtree)
            return node.__class__(node.op, new_children, node.value)

        # Select a random path in the pattern tree to mutate
        paths = get_paths(self.pattern_tree)
        target_path = random.choice(paths)
        new_subtree = PatternTree.random(max_depth=3)
        new_pattern = replace_at_path(self.pattern_tree, target_path, new_subtree)
        return Genome(pattern_tree=new_pattern, fitness=0.0)
    
    def crossover(self, other: 'Genome') -> tuple['Genome', 'Genome']:
        """
        Perform crossover with another genome.
        
        Args:
            other: Parent genome
        
        Returns:
            Two offspring genomes
        """
        # TODO: Implement tree crossover (subtree exchange)
        return self, other
    
    def __repr__(self) -> str:
        return f"Genome(fitness={self.fitness:.4f}, pattern={self.pattern_tree})"

