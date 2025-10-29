#!/usr/bin/env python3
"""
Test code generation with the expanded grammar.

This script generates pattern trees and converts them to TidalCycles code
to verify that all new functions work correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from genetic_music.genome import PatternTree, TidalGrammar, FunctionType
from genetic_music.codegen import to_tidal


def test_all_function_types():
    """Test code generation for each function type."""
    print("=" * 70)
    print("CODE GENERATION TEST - ALL FUNCTION TYPES")
    print("=" * 70)
    
    for func_type in FunctionType:
        print(f"\n{func_type.value.upper().replace('_', ' ')}:")
        print("-" * 70)
        
        funcs = TidalGrammar.get_functions_by_type(func_type)
        
        for sig in funcs[:3]:  # Test first 3 of each type
            # Create a simple pattern for testing
            # Build tree manually to test specific functions
            if func_type == FunctionType.UNARY:
                # Unary: op(sound)
                leaf = PatternTree('sound', [], 'bd')
                tree = PatternTree(sig.name, [leaf], None)
            
            elif func_type in [FunctionType.BINARY_NUMERIC, 
                              FunctionType.BINARY_INT,
                              FunctionType.PROBABILISTIC]:
                # Binary: op(param, sound)
                leaf = PatternTree('sound', [], 'sn')
                param = sig.generate_param()
                tree = PatternTree(sig.name, [leaf], param)
            
            elif func_type == FunctionType.N_ARY:
                # N-ary: op([sound1, sound2, ...])
                children = [
                    PatternTree('sound', [], 'bd'),
                    PatternTree('sound', [], 'sn'),
                ]
                tree = PatternTree(sig.name, children, None)
            
            elif func_type == FunctionType.CONDITIONAL:
                # Conditional: op(n, transform, pattern)
                transform = PatternTree('rev', [PatternTree('sound', [], 'cp')], None)
                pattern = PatternTree('sound', [], 'hh')
                param = sig.generate_param()
                tree = PatternTree(sig.name, [transform, pattern], param)
            
            # Generate code
            code = to_tidal(tree)
            print(f"  {sig.name:15s} -> {code}")


def test_complex_patterns():
    """Test code generation for complex nested patterns."""
    print("\n" + "=" * 70)
    print("COMPLEX NESTED PATTERN GENERATION")
    print("=" * 70)
    
    for i in range(5):
        print(f"\nPattern {i+1}:")
        pattern = PatternTree.random(max_depth=3, method='grow')
        code = to_tidal(pattern)
        print(f"  Tree: {pattern}")
        print(f"  Code: {code}")


def test_specific_patterns():
    """Test specific interesting pattern combinations."""
    print("\n" + "=" * 70)
    print("SPECIFIC PATTERN EXAMPLES")
    print("=" * 70)
    
    examples = [
        ("Simple sound", PatternTree('sound', [], 'bd')),
        ("Fast sound", PatternTree('fast', [PatternTree('sound', [], 'sn')], 2.0)),
        ("Stacked sounds", PatternTree('stack', [
            PatternTree('sound', [], 'bd'),
            PatternTree('sound', [], 'hh'),
            PatternTree('sound', [], 'sn')
        ], None)),
        ("Every with rev", PatternTree('every', [
            PatternTree('rev', [PatternTree('sound', [], 'arpy')], None),
            PatternTree('sound', [], 'bd')
        ], 4)),
        ("Degraded fast pattern", PatternTree('degrade', [
            PatternTree('fast', [PatternTree('sound', [], 'cp')], 3.0)
        ], None)),
    ]
    
    for name, tree in examples:
        code = to_tidal(tree)
        print(f"\n{name}:")
        print(f"  {code}")


def test_all_sounds():
    """Generate patterns with all available sounds."""
    print("\n" + "=" * 70)
    print("SOUND SAMPLE SHOWCASE")
    print("=" * 70)
    
    # Group sounds and generate patterns
    print("\nDrum patterns:")
    drums = ['bd', 'sn', 'cp', 'hh', '808bd']
    for sound in drums[:5]:
        tree = PatternTree('fast', [PatternTree('sound', [], sound)], 2.0)
        print(f"  {to_tidal(tree)}")
    
    print("\nBass patterns:")
    bass = [s for s in TidalGrammar.SOUNDS if 'bass' in s]
    for sound in bass[:3]:
        tree = PatternTree('slow', [PatternTree('sound', [], sound)], 0.5)
        print(f"  {to_tidal(tree)}")
    
    print("\nSynth patterns:")
    synths = [s for s in TidalGrammar.SOUNDS if 'super' in s]
    for sound in synths[:3]:
        tree = PatternTree('rev', [PatternTree('sound', [], sound)], None)
        print(f"  {to_tidal(tree)}")


def test_ready_to_play():
    """Generate actual playable TidalCycles code."""
    print("\n" + "=" * 70)
    print("READY-TO-PLAY TIDALCYCLES PATTERNS")
    print("=" * 70)
    print("\nCopy and paste these into TidalCycles:\n")
    
    for i in range(3):
        pattern = PatternTree.random(max_depth=3, method='grow')
        code = to_tidal(pattern)
        print(f"-- Pattern {i+1}")
        print(f"d{i+1} $ {code}")
        print()


def main():
    """Run all tests."""
    print("\n" + "█" * 70)
    print("TIDALCYCLES CODE GENERATION TEST".center(70))
    print("█" * 70)
    
    test_all_function_types()
    test_specific_patterns()
    test_all_sounds()
    test_complex_patterns()
    test_ready_to_play()
    
    print("\n" + "=" * 70)
    print("Code generation test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

