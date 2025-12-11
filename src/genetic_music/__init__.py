"""
Genetic Evolution of Music
A music generation system using genetic programming to evolve
TidalCycles patterns.
"""

"""Genetic Music Generation with TidalCycles.

A framework for evolving musical patterns using genetic algorithms,
with TidalCycles as the backend for pattern generation and playback.
"""

from .genome.genome import Genome
from .tree.pattern_tree import PatternTree
from .backend.backend import Backend
from .genome.population import evolve_population
from .codegen.tidal_codegen import to_tidal
from .config import config, get_boot_tidal_path

__all__ = [
    "Genome",
    "PatternTree",
    "Backend",
    "evolve_population",
    "to_tidal",
    "config",
    "get_boot_tidal_path",
]
__version__ = "0.1.0"
