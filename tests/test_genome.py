"""
Tests for genome module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genetic_music.genome import Genome, PatternTree, SynthTree


def test_pattern_tree_creation():
    """Test random pattern tree generation."""
    tree = PatternTree.random(max_depth=3)
    assert tree is not None
    assert tree.depth() <= 3
    print(f"✓ Pattern tree created: {tree}")


def test_synth_tree_creation():
    """Test random synth tree generation."""
    tree = SynthTree.random(max_depth=3)
    assert tree is not None
    assert tree.depth() <= 3
    print(f"✓ Synth tree created: {tree}")


def test_genome_creation():
    """Test genome creation."""
    genome = Genome.random()
    assert genome.pattern_tree is not None
    assert genome.synth_tree is not None
    assert genome.fitness == 0.0
    print(f"✓ Genome created: {genome}")


def test_tree_properties():
    """Test tree properties."""
    pattern = PatternTree.random(max_depth=4)
    
    depth = pattern.depth()
    size = pattern.size()
    
    assert depth >= 1
    assert size >= 1
    assert depth <= 4
    
    print(f"✓ Tree properties: depth={depth}, size={size}")


if __name__ == "__main__":
    print("Running tests...\n")
    
    test_pattern_tree_creation()
    test_synth_tree_creation()
    test_genome_creation()
    test_tree_properties()
    
    print("\n✓ All tests passed!")

