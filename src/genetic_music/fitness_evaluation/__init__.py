from __future__ import annotations

"""Fitness evaluation for genetic music generation.

This package provides utilities for evaluating pattern fitness based on
audio feature similarity to a target audio file.

Public API
----------
From :mod:`.fitness_evaluation`:
    - :func:`evaluate_genome_fitness` - Evaluate genome fitness (main entry point)
    - :func:`get_fitness` - Convenience function with defaults
    - :func:`feature_similarity` - Extract and compare audio features
    - :func:`compute_fitness` - Weighted fitness aggregation
    - :data:`DEFAULT_WEIGHTS` - Default feature weights
    - :func:`dominates` - Multi-objective dominance check
    - :func:`pareto_front` - Pareto front computation
"""

from .fitness_evaluation import (
    DEFAULT_WEIGHTS,
    compute_fitness,
    # dominates,
    evaluate_genome_fitness,
    feature_similarity,
    get_fitness,
    # pareto_front,
)

__all__ = [
    "evaluate_genome_fitness",
    "get_fitness",
    "feature_similarity",
    "compute_fitness",
    "DEFAULT_WEIGHTS",
    # "dominates",
    # "pareto_front",
]
