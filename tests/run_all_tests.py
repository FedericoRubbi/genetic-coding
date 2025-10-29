#!/usr/bin/env python3
"""
Master test runner for the genetic music evolution project.

This script runs all tests in the recommended order:
1. Unit tests (pytest)
2. SuperCollider integration test
3. SuperDirt integration test
4. TidalCycles integration test

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --unit       # Unit tests only
    python tests/run_all_tests.py --integration # Integration tests only
"""

import sys
import subprocess
import argparse
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def run_command(cmd, description):
    """Run a command and return success status."""
    print_header(description)
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
        return True
    else:
        print(f"\n❌ {description} - FAILED")
        return False


def run_unit_tests():
    """Run pytest unit tests."""
    print_header("UNIT TESTS")
    
    test_files = [
        "tests/test_genome.py",
        "tests/test_codegen.py"
    ]
    
    results = []
    
    for test_file in test_files:
        if Path(test_file).exists():
            success = run_command(
                ["pytest", test_file, "-v"],
                f"Unit Test: {test_file}"
            )
            results.append((test_file, success))
        else:
            print(f"⚠️  Warning: {test_file} not found")
    
    return results


def run_integration_tests():
    """Run integration tests."""
    print_header("INTEGRATION TESTS")
    
    print("\n⚠️  Integration tests require external services:")
    print("   - SuperCollider with SuperDirt running")
    print("   - Audio output enabled")
    print("\nMake sure SuperCollider is set up before continuing.")
    print("See scripts/setup_supercollider.md for instructions.\n")
    
    response = input("Continue with integration tests? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Skipping integration tests.")
        return []
    
    test_files = [
        "tests/test_supercollider.py",
        "tests/test_superdirt.py",
        "tests/test_tidalcycles.py"
    ]
    
    results = []
    
    for test_file in test_files:
        if Path(test_file).exists():
            success = run_command(
                ["python", test_file],
                f"Integration Test: {test_file}"
            )
            results.append((test_file, success))
            
            if not success:
                print(f"\n⚠️  {test_file} failed. Continue anyway? (y/n): ", end="")
                if input().strip().lower() != 'y':
                    print("Stopping integration tests.")
                    break
        else:
            print(f"⚠️  Warning: {test_file} not found")
    
    return results


def print_summary(unit_results, integration_results):
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    all_results = unit_results + integration_results
    
    if not all_results:
        print("No tests were run.")
        return False
    
    # Unit tests
    if unit_results:
        print("\nUnit Tests:")
        for test_file, success in unit_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {test_file}")
    
    # Integration tests
    if integration_results:
        print("\nIntegration Tests:")
        for test_file, success in integration_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {test_file}")
    
    # Overall summary
    total_tests = len(all_results)
    passed_tests = sum(1 for _, success in all_results if success)
    
    print(f"\nTotal: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test suite(s) failed.")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Run genetic music evolution tests"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    
    args = parser.parse_args()
    
    print_header("🎵 Genetic Music Evolution Test Suite")
    
    unit_results = []
    integration_results = []
    
    # Determine what to run
    run_unit = args.unit or not args.integration
    run_integration = args.integration or not args.unit
    
    # Run tests
    if run_unit:
        unit_results = run_unit_tests()
    
    if run_integration:
        integration_results = run_integration_tests()
    
    # Print summary
    success = print_summary(unit_results, integration_results)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

