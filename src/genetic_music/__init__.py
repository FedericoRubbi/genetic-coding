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
from .codegen.tidal_codegen import to_tidal
from .backend.backend import Backend
from .grammar.tidal_grammar import TidalGrammar
from .genome.population import evolve_population

__all__ = [
    'Genome',
    'PatternTree',
    'to_tidal',
    'Backend',
    'TidalGrammar',
    'evolve_population'
]
__version__ = "0.1.0"
