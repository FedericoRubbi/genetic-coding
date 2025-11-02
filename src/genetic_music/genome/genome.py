"""Genome representation for TidalCycles musical patterns."""

from dataclasses import dataclass
import random
from typing import List, Optional
from ..tree.pattern_tree import PatternTree
from ..tree.node import TreeNode


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
        # For now, just return copies of parents
        return self, other
    
    def __repr__(self) -> str:
        return f"Genome(fitness={self.fitness:.4f}, pattern={self.pattern_tree})"