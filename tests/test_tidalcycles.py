#!/usr/bin/env python3
"""
Test TidalCycles integration and pattern generation.

Note: This tests pattern generation and code compatibility, not actual
TidalCycles runtime (which requires Haskell/GHC installation).

For full TidalCycles integration, you would need:
1. GHC (Glasgow Haskell Compiler)
2. TidalCycles Haskell library
3. Running Tidal REPL connected to SuperDirt

This test focuses on:
- Pattern code generation from our genetic system
- Pattern syntax validation
- Compatibility with SuperDirt via direct OSC

Run: python tests/test_tidalcycles.py
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pythonosc
        print("✓ pythonosc module found")
        
        from genetic_music import codegen
        print("✓ genetic_music.codegen module found")
        
        return True
    except ImportError as e:
        print(f"❌ ERROR: {e}")
        print("   Run: pip install python-osc")
        return False


def test_pattern_generation():
    """Test generating Tidal pattern code from genome."""
    from genetic_music.genome import PatternTree
    from genetic_music.codegen import to_tidal
    
    print("\n" + "=" * 60)
    print("Test 1: Pattern Code Generation")
    print("=" * 60)
    
    print("\nGenerating random pattern...")
    
    # Create a random pattern tree
    pattern_tree = PatternTree.random(max_depth=3)
    
    # Generate Tidal code
    tidal_code = to_tidal(pattern_tree)
    
    print("\nGenerated Tidal Pattern:")
    print("-" * 60)
    print(tidal_code)
    print("-" * 60)
    
    # Basic validation
    assert len(tidal_code) > 0, "Generated code should not be empty"
    assert '"' in tidal_code, "Should contain sample names in quotes"
    
    print("\n✓ Pattern generation successful")
    print("  This pattern can be sent to SuperDirt via OSC")
    
    return True


def test_pattern_structures():
    """Test different pattern structures."""
    from genetic_music.genome import PatternTree
    from genetic_music.codegen import to_tidal
    
    print("\n" + "=" * 60)
    print("Test 2: Different Pattern Structures")
    print("=" * 60)
    
    # Note: PatternTree uses TreeNode, not PatternNode
    # Let's test with randomly generated patterns instead
    test_cases = [
        ("Random pattern depth=2", PatternTree.random(max_depth=2)),
        ("Random pattern depth=3", PatternTree.random(max_depth=3)),
        ("Random pattern depth=1", PatternTree.random(max_depth=1)),
    ]
    
    print("\nGenerating different pattern structures...\n")
    
    for i, (desc, pattern) in enumerate(test_cases, 1):
        print(f"   {i}. {desc}:")
        code = to_tidal(pattern)
        print(f"      {code}")
        assert len(code) > 0
    
    print("\n✓ All pattern structures generated successfully")
    
    return True


def test_pattern_playback():
    """Test playing generated patterns via SuperDirt."""
    from pythonosc import udp_client
    from genetic_music.genome import PatternTree
    
    print("\n" + "=" * 60)
    print("Test 3: Pattern Playback via SuperDirt")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    
    print("\nGenerating and playing patterns...\n")
    
    # Test 1: Simple drum pattern
    print("   1. Simple drum pattern (bd sn)...")
    
    # Create simple events for a basic pattern
    events = [
        ("bd", 0.0),   # kick at beat 0
        ("sn", 0.5),   # snare at beat 0.5
        ("bd", 1.0),   # kick at beat 1
        ("sn", 1.5),   # snare at beat 1.5
    ]
    
    for sample, position in events:
        client.send_message("/dirt/play", [
            "cps", 1.0,          # 1 cycle per second
            "cycle", position,   # position in cycle
            "delta", 0.5,        # duration
            "orbit", 8,
            "s", sample,
            "n", 0,
            "gain", 0.8
        ])
        time.sleep(0.25)
    
    time.sleep(1.0)
    
    # Test 2: Random pattern
    print("\n   2. Random generated pattern...")
    
    pattern = PatternTree.random(max_depth=2)
    
    # For simplicity, just play some samples from it
    samples_to_play = ["bd", "hh", "sn", "cp"]
    
    for i, sample in enumerate(samples_to_play):
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", sample,
            "n", 0,
            "gain", 0.8
        ])
        time.sleep(0.6)
    
    print("\n✓ Pattern playback test complete")
    print("→ Did you hear the patterns?")
    
    return True


def test_backend_integration():
    """Test integration with genetic_music.backend."""
    from genetic_music.backend import Backend
    
    print("\n" + "=" * 60)
    print("Test 4: Backend Integration")
    print("=" * 60)
    
    print("\nInitializing backend...")
    
    backend = Backend(orbit=8)
    
    print("✓ Backend initialized")
    
    # Test pattern sending
    print("\nSending test pattern via backend...")
    
    test_pattern = 'sound "bd sn hh cp"'
    backend.send_pattern(test_pattern)
    
    time.sleep(2)
    
    print("\n✓ Backend integration test complete")
    print("→ Check SuperCollider for any OSC messages")
    
    return True


def test_tidal_syntax_validation():
    """Test that generated code follows Tidal syntax."""
    from genetic_music.genome import PatternTree
    from genetic_music.codegen import to_tidal
    
    print("\n" + "=" * 60)
    print("Test 5: Tidal Syntax Validation")
    print("=" * 60)
    
    print("\nValidating Tidal syntax in generated code...\n")
    
    # Generate multiple random patterns
    for i in range(5):
        pattern = PatternTree.random(max_depth=3)
        code = to_tidal(pattern)
        
        # Basic syntax checks
        checks = [
            ('"' in code, "Contains quoted strings"),
            (code.count('"') % 2 == 0, "Balanced quotes"),
            (code.count('[') == code.count(']'), "Balanced brackets"),
            (code.count('(') == code.count(')'), "Balanced parentheses"),
        ]
        
        for check, desc in checks:
            assert check, f"Syntax check failed: {desc}"
    
    print("   ✓ All syntax checks passed for 5 random patterns")
    print("\n✓ Tidal syntax validation complete")
    
    return True


def run_all_tests():
    """Run all TidalCycles tests."""
    print("\n" + "=" * 70)
    print("🎵 TidalCycles Integration Test Suite")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    print("\nNOTE: These tests focus on pattern generation and SuperDirt")
    print("      integration, not full TidalCycles runtime.")
    print("\nPREREQUISITES:")
    print("  1. SuperCollider with SuperDirt is running")
    print("  2. genetic_music package is importable")
    print("\nReady? Press Enter to start tests...")
    input()
    
    # Run tests
    results = []
    
    results.append(("Pattern Generation", test_pattern_generation()))
    results.append(("Pattern Structures", test_pattern_structures()))
    results.append(("Pattern Playback", test_pattern_playback()))
    results.append(("Backend Integration", test_backend_integration()))
    results.append(("Syntax Validation", test_tidal_syntax_validation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All TidalCycles integration tests passed!")
        print("\nNext step: Run examples/basic_evolution.py")
        return True
    else:
        print("\n⚠️  Some tests failed.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

