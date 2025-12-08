from __future__ import annotations

"""Genome and population evolution for genetic music generation.

This package provides the core evolutionary structures:
- :class:`Genome` - Container for pattern trees with fitness and genetic operators
- :func:`evolve_population` - Population-level selection and reproduction

Public API
----------
From :mod:`.genome`:
    - :class:`Genome` - Pattern genome with mutation and crossover

From :mod:`.population`:
    - :func:`evolve_population` - Evolve a population for one generation
"""

from .genome import Genome
from .population import evolve_population

__all__ = [
    "Genome",
    "evolve_population",
]
