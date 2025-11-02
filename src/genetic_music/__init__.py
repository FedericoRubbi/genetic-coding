"""
Genetic Evolution of Music
A music generation system using genetic programming to evolve
TidalCycles patterns.
"""

__version__ = "0.1.0"

from .genome import Genome, PatternTree
from .codegen import to_tidal
from .backend import Backend
from .fitness import compute_fitness
from .evolve import evolve_population

__all__ = [
    "Genome",
    "PatternTree",
    "to_tidal",
    "Backend",
    "compute_fitness",
    "evolve_population",
]