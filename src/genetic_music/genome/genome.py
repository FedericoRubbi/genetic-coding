"""Genome representation for TidalCycles musical patterns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

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
        """Return a (currently unmutated) copy of this genome.

        Mutation of the underlying tree structure is left for future work;
        for now we return a shallow copy so the evolutionary loop can run.
        """
        # Shallow copy is sufficient while we have no in-place mutation.
        return Genome(pattern_tree=self.pattern_tree, fitness=self.fitness)

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