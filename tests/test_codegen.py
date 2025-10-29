"""
Tests for code generation module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genetic_music.genome import PatternTree, SynthTree
from genetic_music.codegen import to_tidal, to_supercollider


def test_tidal_codegen():
    """Test Tidal code generation."""
    # Create a simple pattern
    pattern = PatternTree('sound', [], 'bd')
    code = to_tidal(pattern)
    assert 'sound' in code
    assert 'bd' in code
    print(f"✓ Simple pattern: {code}")
    
    # Create a complex pattern
    pattern = PatternTree.random(max_depth=3)
    code = to_tidal(pattern)
    assert len(code) > 0
    print(f"✓ Complex pattern: {code}")


def test_supercollider_codegen():
    """Test SuperCollider code generation."""
    # Create a simple synth
    synth = SynthTree('SinOsc', [], 440)
    code = to_supercollider(synth, 'test')
    assert 'SynthDef' in code
    assert 'test' in code
    print(f"✓ Simple synth generated")
    
    # Create a complex synth
    synth = SynthTree.random(max_depth=3)
    code = to_supercollider(synth, 'complex')
    assert 'SynthDef' in code
    assert len(code) > 0
    print(f"✓ Complex synth: {code[:100]}...")


if __name__ == "__main__":
    print("Running code generation tests...\n")
    
    test_tidal_codegen()
    test_supercollider_codegen()
    
    print("\n✓ All tests passed!")

