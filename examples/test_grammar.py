#!/usr/bin/env python3
"""
Test and demonstrate the TidalCycles grammar system.

This script generates random pattern trees using the grammar
and shows the expanded vocabulary and function types.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from genetic_music.genome import (
    PatternTree, 
    TidalGrammar, 
    FunctionType,
    Genome
)


def test_grammar_functions():
    """Display all available functions organized by type."""
    print("=" * 70)
    print("TIDALCYCLES GRAMMAR - AVAILABLE FUNCTIONS")
    print("=" * 70)
    
    for func_type in FunctionType:
        funcs = TidalGrammar.get_functions_by_type(func_type)
        if funcs:
            print(f"\n{func_type.value.upper().replace('_', ' ')}:")
            print("-" * 70)
            for sig in funcs:
                param_info = ""
                if sig.param_generator:
                    # Generate sample param to show range
                    samples = [sig.generate_param() for _ in range(3)]
                    param_info = f" (e.g., {samples[0]:.2f})"
                child_info = ""
                if sig.min_children == sig.max_children:
                    child_info = f" [{sig.min_children} child(ren)]"
                else:
                    child_info = f" [{sig.min_children}-{sig.max_children} children]"
                print(f"  • {sig.name:15s}{param_info:20s}{child_info}")


def test_sound_samples():
    """Display all available sound samples."""
    print("\n" + "=" * 70)
    print("AVAILABLE SOUND SAMPLES")
    print("=" * 70)
    
    # Group sounds by category
    drums = [s for s in TidalGrammar.SOUNDS if s in 
             ['bd', 'sn', 'cp', 'hh', 'oh', 'ch', 'cy', 'rim', 'tom', 'clap', 'click']]
    bass_sounds = [s for s in TidalGrammar.SOUNDS if 'bass' in s.lower()]
    synths = [s for s in TidalGrammar.SOUNDS if 'super' in s.lower()]
    breaks = [s for s in TidalGrammar.SOUNDS if 'break' in s.lower() or 'amen' in s.lower()]
    drums_808_909 = [s for s in TidalGrammar.SOUNDS if '808' in s or '909' in s]
    
    print(f"\nDrums ({len(drums)}): {', '.join(drums)}")
    print(f"\nBass ({len(bass_sounds)}): {', '.join(bass_sounds)}")
    print(f"\nSynths ({len(synths)}): {', '.join(synths)}")
    print(f"\nBreaks ({len(breaks)}): {', '.join(breaks)}")
    print(f"\n808/909 ({len(drums_808_909)}): {', '.join(drums_808_909)}")
    
    other = [s for s in TidalGrammar.SOUNDS if s not in 
             drums + bass_sounds + synths + breaks + drums_808_909]
    if other:
        print(f"\nOther ({len(other)}): {', '.join(other)}")
    
    print(f"\n{'Total Samples:':<20} {len(TidalGrammar.SOUNDS)}")


def test_pattern_generation():
    """Generate and display sample pattern trees."""
    print("\n" + "=" * 70)
    print("SAMPLE PATTERN TREE GENERATION")
    print("=" * 70)
    
    for i in range(5):
        print(f"\nPattern {i+1}:")
        pattern = PatternTree.random(max_depth=3, method='grow')
        print(f"  Depth: {pattern.depth()}, Size: {pattern.size()} nodes")
        print(f"  Tree: {pattern}")


def test_genome_generation():
    """Generate complete genomes."""
    print("\n" + "=" * 70)
    print("COMPLETE GENOME GENERATION")
    print("=" * 70)
    
    for i in range(3):
        print(f"\nGenome {i+1}:")
        genome = Genome.random(pattern_depth=3, synth_depth=3)
        print(f"  Pattern: {genome.pattern_tree}")
        print(f"  Synth: {genome.synth_tree}")
        print(f"  Pattern stats: depth={genome.pattern_tree.depth()}, size={genome.pattern_tree.size()}")


def compare_old_vs_new():
    """Compare old and new vocabulary size."""
    print("\n" + "=" * 70)
    print("VOCABULARY EXPANSION")
    print("=" * 70)
    
    # Old vocabulary (from original code)
    old_combinators = ['fast', 'slow', 'every', 'rev', 'stack', 'cat', 'density']
    old_sounds = ['bd', 'sn', 'cp', 'hh', 'oh', 'ch', 'arpy', 'bass']
    
    # New vocabulary
    new_functions = list(TidalGrammar.FUNCTIONS.keys())
    new_sounds = TidalGrammar.SOUNDS
    
    print(f"\nFunctions:")
    print(f"  Old: {len(old_combinators)} functions")
    print(f"  New: {len(new_functions)} functions")
    print(f"  Increase: +{len(new_functions) - len(old_combinators)} functions ({(len(new_functions) / len(old_combinators) * 100 - 100):.0f}% increase)")
    
    print(f"\nSound Samples:")
    print(f"  Old: {len(old_sounds)} samples")
    print(f"  New: {len(new_sounds)} samples")
    print(f"  Increase: +{len(new_sounds) - len(old_sounds)} samples ({(len(new_sounds) / len(old_sounds) * 100 - 100):.0f}% increase)")
    
    print(f"\nNew functions added: {', '.join([f for f in new_functions if f not in old_combinators])}")


def main():
    """Run all tests."""
    print("\n" + "█" * 70)
    print("TIDALCYCLES GRAMMAR SYSTEM TEST".center(70))
    print("█" * 70)
    
    compare_old_vs_new()
    test_grammar_functions()
    test_sound_samples()
    test_pattern_generation()
    test_genome_generation()
    
    print("\n" + "=" * 70)
    print("For more information, see docs/TIDAL_GRAMMAR.md")
    print("=" * 70)


if __name__ == "__main__":
    main()

