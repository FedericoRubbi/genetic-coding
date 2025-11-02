# tidal_gen/generator/typed_generator.py
from ..tree.pattern_tree import PatternTree
from ..grammar.tidal_type import TidalType

def generate_control_pattern(max_depth=4):
    """Always produce a ControlPattern-rooted tree."""
    tree = PatternTree.random(TidalType.CONTROL, max_depth)
    # Optionally add modifiers
    # TODO: can insert 0–N modifiers on top
    return tree