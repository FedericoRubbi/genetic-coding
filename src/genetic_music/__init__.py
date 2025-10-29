"""
Genetic Co-Evolution of Music
A music generation system using genetic programming to evolve
TidalCycles patterns and SuperCollider synths.
"""

__version__ = "0.1.0"

from .genome import Genome, PatternTree, SynthTree
from .codegen import to_tidal, to_supercollider
from .backend import Backend
from .fitness import compute_fitness
from .evolve import evolve_population

__all__ = [
    "Genome",
    "PatternTree",
    "SynthTree",
    "to_tidal",
    "to_supercollider",
    "Backend",
    "compute_fitness",
    "evolve_population",
]

