"""Genome representation for TidalCycles musical patterns."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence, Tuple

from genetic_music.generator.generation import (
    mutate_pattern_tree,
    _iter_nodes_with_paths,
    _clone_with_replacement,
)
from genetic_music.tree.pattern_tree import PatternTree


@dataclass
class Genome:
    """Complete genome containing a pattern tree and its fitness score."""

    pattern_tree: PatternTree
    fitness: float = 0.0

    @classmethod
    def random(cls, pattern_tree: PatternTree) -> "Genome":
        """Create a genome from a randomly generated :class:`PatternTree`.

        Random pattern generation is handled elsewhere (e.g. via the
        ``genetic_music.generator.generation`` utilities), so this method
        simply wraps an already-generated tree.
        """
        return cls(pattern_tree=pattern_tree, fitness=0.0)

    def mutate(
        self,
        rate: float = 0.1,
        *,
        use_target: bool = False,
        min_length: int = 1,
        max_examples: int = 50,
        use_tree_metrics: bool = True,
        mutation_kinds: Sequence[str] | None = None,
    ) -> "Genome":
        """Return a mutated copy of this genome.

        With probability ``rate`` a single mutation operator is applied to the
        underlying :class:`PatternTree`.  If mutation is not applied, or if the
        operator makes no structural change, a structurally identical copy of
        this genome is returned.

        Args:
            rate: Probability of applying mutation.
            use_target: Whether to use target pattern information during
                mutation.
            min_length: Minimum length of generated patterns.
            max_examples: Maximum number of examples to consider during mutation.
            use_tree_metrics: Whether to use tree metrics during mutation.
            mutation_kinds: Sequence of mutation operator kinds to consider. If
                ``None``, all available mutation operators are used. If not 
                ``None``, only the specified mutation operators are considered. Check
                the documentation of ``mutate_pattern_tree`` for valid kinds.
        """
        # Decide whether to mutate this genome at all.
        if random.random() > rate:
            return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness)

        mutated_tree = mutate_pattern_tree(
            self.pattern_tree,
            mutation_kinds=mutation_kinds, # by default all mutation kinds
            use_target=use_target,
            min_length=min_length,
            max_examples=max_examples,
            use_tree_metrics=use_tree_metrics,
        )
        # If nothing changed, keep fitness; otherwise reset so it is recomputed.
        if mutated_tree is self.pattern_tree:
            return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness)

        return Genome(pattern_tree=mutated_tree, fitness=0.0)

    def crossover(self, other: "Genome") -> Tuple["Genome", "Genome"]:
        """Perform crossover with another genome.

        Finds all matching nodes (by .op) in both trees, randomly selects a pair,
        and swaps their subtrees.
        """
        # Get all nodes with paths
        nodes_self = _iter_nodes_with_paths(self.pattern_tree.root)
        nodes_other = _iter_nodes_with_paths(other.pattern_tree.root)

        # Group by op
        ops_self = {}
        for path, node in nodes_self:
            if node.op not in ops_self:
                ops_self[node.op] = []
            ops_self[node.op].append((path, node))

        ops_other = {}
        for path, node in nodes_other:
            if node.op not in ops_other:
                ops_other[node.op] = []
            ops_other[node.op].append((path, node))

        # Find common ops
        common_ops = list(set(ops_self.keys()) & set(ops_other.keys()))

        if not common_ops:
            # No matching ops, return clones
            return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness), Genome(
                pattern_tree=other.pattern_tree,
                fitness=other.fitness,
            )

        # Randomly choose an op and one node from each tree
        chosen_op = random.choice(common_ops)
        path_self, node_self = random.choice(ops_self[chosen_op])
        path_other, node_other = random.choice(ops_other[chosen_op])

        # Swap subtrees
        # New self root: replace node at path_self with node_other
        new_root_self = _clone_with_replacement(self.pattern_tree.root, path_self, node_other)

        # New other root: replace node at path_other with node_self
        new_root_other = _clone_with_replacement(other.pattern_tree.root, path_other, node_self)

        # Return new Genomes
        return (
            Genome(pattern_tree=PatternTree(root=new_root_self), fitness=0.0),
            Genome(pattern_tree=PatternTree(root=new_root_other), fitness=0.0),
        )

    def __repr__(self) -> str:
        return f"Genome(fitness={self.fitness:.4f}, pattern={self.pattern_tree})"