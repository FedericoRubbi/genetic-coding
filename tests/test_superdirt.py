#!/usr/bin/env python3
"""
Test SuperDirt OSC communication and sample playback.

Prerequisites:
1. SuperCollider is open with server booted
2. SuperDirt is started (see scripts/setup_supercollider.md)
3. Samples are loaded: ~dirt.loadSoundFiles;
4. All orbits are audible: ~dirt.start(57120, Array.fill(12, 0));

Run: python tests/test_superdirt.py
"""

import sys
import time


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pythonosc
        print("✓ pythonosc module found")
        return True
    except ImportError:
        print("❌ ERROR: pythonosc not installed")
        print("   Run: pip install python-osc")
        return False


def test_superdirt_connection():
    """Test basic connection to SuperDirt."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 1: SuperDirt Connection")
    print("=" * 60)
    
    # SuperDirt default port
    host = "127.0.0.1"
    port = 57120
    
    print(f"\nConnecting to SuperDirt at {host}:{port}...")
    
    try:
        client = udp_client.SimpleUDPClient(host, port)
        print("✓ OSC client created for SuperDirt")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_basic_samples():
    """Test basic drum samples."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 2: Basic Drum Samples")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    
    # Test common drum samples
    samples = [
        ("bd", "Kick Drum"),
        ("sn", "Snare"),
        ("hh", "Hi-Hat"),
        ("cp", "Clap")
    ]
    
    print("\nPlaying drum samples...")
    print("(You should hear each sound)\n")
    
    for i, (sample_name, description) in enumerate(samples):
        print(f"   {i+1}. {description} ('{sample_name}')...")
        
        client.send_message("/dirt/play", [
            "cps", 0.5,          # cycles per second
            "cycle", 0.0,        # cycle position
            "delta", 1.0,        # event duration
            "orbit", 8,          # orbit number (GP system)
            "s", sample_name,    # sound name
            "n", 0,              # sound variant
            "gain", 1.0          # volume
        ])
        
        time.sleep(1.0)
    
    print("\n✓ All drum samples sent")
    print("→ Did you hear all 4 sounds?")
    
    return True


def test_different_orbits():
    """Test multiple orbits."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 3: Multiple Orbits")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    
    print("\nTesting orbits 0, 8, and 11...")
    print("(Each should play a kick drum)\n")
    
    orbits = [0, 8, 11]
    
    for orbit in orbits:
        print(f"   Playing on orbit {orbit}...")
        
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", orbit,
            "s", "bd",
            "n", 0,
            "gain", 1.0
        ])
        
        time.sleep(0.8)
    
    print("\n✓ Multi-orbit test complete")
    print("→ Did you hear 3 kick drums?")
    
    return True


def test_sample_parameters():
    """Test sample parameters (gain, speed, pan)."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 4: Sample Parameters")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    
    print("\nTesting different parameters...\n")
    
    # Test 1: Different gains
    print("   1. Testing volume (gain)...")
    for gain in [0.3, 0.6, 1.0]:
        print(f"      Gain = {gain}")
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "bd",
            "n", 0,
            "gain", gain
        ])
        time.sleep(0.6)
    
    # Test 2: Different speeds
    print("\n   2. Testing playback speed...")
    for speed in [0.5, 1.0, 2.0]:
        print(f"      Speed = {speed}")
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "sn",
            "n", 0,
            "speed", speed,
            "gain", 0.8
        ])
        time.sleep(0.6)
    
    # Test 3: Different pan positions
    print("\n   3. Testing stereo panning...")
    for pan in [0.0, 0.5, 1.0]:
        pan_desc = ["Left", "Center", "Right"][int(pan * 2)]
        print(f"      Pan = {pan} ({pan_desc})")
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "hh",
            "n", 0,
            "pan", pan,
            "gain", 0.8
        ])
        time.sleep(0.6)
    
    print("\n✓ Parameter tests complete")
    print("→ Did you notice the changes in volume, speed, and panning?")
    
    return True


def test_sample_variants():
    """Test different sample variants."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 5: Sample Variants")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    
    print("\nTesting sample variants (different 'n' values)...")
    print("(Different variants of the same sample)\n")
    
    # Many samples have multiple variants (n=0, n=1, n=2, etc.)
    for n in range(4):
        print(f"   Playing arpy:{n}...")
        
        client.send_message("/dirt/play", [
            "cps", 0.5,
            "cycle", 0.0,
            "delta", 1.0,
            "orbit", 8,
            "s", "arpy",
            "n", n,
            "gain", 0.8
        ])
        
        time.sleep(0.7)
    
    print("\n✓ Sample variant tests complete")
    print("→ Did you hear 4 different variations?")
    
    return True


def run_all_tests():
    """Run all SuperDirt tests."""
    print("\n" + "=" * 70)
    print("🎵 SuperDirt Test Suite")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    print("\nPREREQUISITES:")
    print("  1. SuperCollider is open with server booted")
    print("  2. SuperDirt is started:")
    print("     ~dirt = SuperDirt(2, s);")
    print("     ~dirt.loadSoundFiles;")
    print("     ~dirt.start(57120, Array.fill(12, 0));")
    print("  3. OSC monitoring enabled (optional):")
    print("     OSCdef(\\test, {|msg| msg.postln}, '/dirt/play');")
    print("\nReady? Press Enter to start tests...")
    input()
    
    # Run tests
    results = []
    
    results.append(("SuperDirt Connection", test_superdirt_connection()))
    results.append(("Basic Drum Samples", test_basic_samples()))
    results.append(("Multiple Orbits", test_different_orbits()))
    results.append(("Sample Parameters", test_sample_parameters()))
    results.append(("Sample Variants", test_sample_variants()))
    
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
        print("\n🎉 All SuperDirt tests passed!")
        print("\nNext step: Test integration with genetic_music.backend")
        return True
    else:
        print("\n⚠️  Some tests failed. Check SuperDirt setup.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

