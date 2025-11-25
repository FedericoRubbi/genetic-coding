"""Genome representation for TidalCycles musical patterns."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Tuple

from genetic_music.generator.generation import mutate_pattern_tree
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

    def mutate(self, rate: float = 0.1) -> "Genome":
        """Return a mutated copy of this genome.

        With probability ``rate`` a single subtree of the underlying
        :class:`PatternTree` is replaced by a newly generated subtree that is
        syntactically valid according to the Lark grammar.  If mutation is not
        applied, or if subtree generation fails, a structurally identical copy
        of this genome is returned.
        """
        # Decide whether to mutate this genome at all.
        if random.random() > rate:
            return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness)

        mutated_tree = mutate_pattern_tree(self.pattern_tree)
        # If nothing changed, keep fitness; otherwise reset so it is recomputed.
        if mutated_tree is self.pattern_tree:
            return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness)

        return Genome(pattern_tree=mutated_tree, fitness=0.0)

    def crossover(self, other: "Genome") -> Tuple["Genome", "Genome"]:
        """Perform crossover with another genome.

        Tree crossover (subtree exchange) is not yet implemented; this method
        currently returns unchanged copies of the parents to keep the API
        stable for the evolutionary loop.
        """
        return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness), Genome(
            pattern_tree=other.pattern_tree,
            fitness=other.fitness,
        )

    def __repr__(self) -> str:
        return f"Genome(fitness={self.fitness:.4f}, pattern={self.pattern_tree})"