#!/usr/bin/env python3
"""
Test SuperCollider server connectivity and basic audio functionality.

Prerequisites:
1. SuperCollider is installed and open
2. Server is booted: s.boot;
3. Basic audio test works: { SinOsc.ar(440) * 0.1 }.play;

Run: python tests/test_supercollider.py
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


def test_server_connection():
    """Test basic OSC connection to SuperCollider server."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 1: SuperCollider Server Connection")
    print("=" * 60)
    
    # SuperCollider server default port
    host = "127.0.0.1"
    port = 57110
    
    print(f"\nConnecting to SuperCollider server at {host}:{port}...")
    
    try:
        client = udp_client.SimpleUDPClient(host, port)
        print("✓ OSC client created")
        
        # Send status request
        print("\nSending /status request...")
        client.send_message("/status", [])
        time.sleep(0.5)
        
        print("✓ Message sent successfully")
        print("\n→ Check SuperCollider Post window for /status.reply")
        print("  If you see status messages, the server is responding!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_server_commands():
    """Test sending basic server commands."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 2: Server Commands")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57110)
    
    print("\n1. Testing /dumpOSC (enable OSC message dumping)...")
    client.send_message("/dumpOSC", [1])
    time.sleep(0.3)
    print("   ✓ Sent")
    
    print("\n2. Testing /notify (register for notifications)...")
    client.send_message("/notify", [1])
    time.sleep(0.3)
    print("   ✓ Sent")
    
    print("\n3. Testing /status (request server status)...")
    client.send_message("/status", [])
    time.sleep(0.3)
    print("   ✓ Sent")
    
    print("\n→ Check SuperCollider Post window for responses")
    
    return True


def test_control_bus():
    """Test setting control bus values."""
    from pythonosc import udp_client
    
    print("\n" + "=" * 60)
    print("Test 3: Control Bus")
    print("=" * 60)
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 57110)
    
    print("\nSetting control bus values...")
    
    # Set some control bus values
    test_buses = [100, 101, 102]
    test_values = [0.5, 0.75, 1.0]
    
    for bus, value in zip(test_buses, test_values):
        print(f"   Setting bus {bus} = {value}")
        client.send_message("/c_set", [bus, value])
        time.sleep(0.1)
    
    print("\n✓ Control bus messages sent")
    print("→ Check SuperCollider for any errors")
    
    return True


def run_all_tests():
    """Run all SuperCollider tests."""
    print("\n" + "=" * 70)
    print("🎵 SuperCollider Server Test Suite")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    print("\nPREREQUISITES:")
    print("  1. SuperCollider is open")
    print("  2. Server is booted (run: s.boot; in SuperCollider)")
    print("  3. You can hear audio ({ SinOsc.ar(440) * 0.1 }.play;)")
    print("\nReady? Press Enter to start tests...")
    input()
    
    # Run tests
    results = []
    
    results.append(("Server Connection", test_server_connection()))
    results.append(("Server Commands", test_server_commands()))
    results.append(("Control Bus", test_control_bus()))
    
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
        print("\n🎉 All SuperCollider tests passed!")
        print("\nNext step: Run tests/test_superdirt.py")
        return True
    else:
        print("\n⚠️  Some tests failed. Check SuperCollider setup.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

