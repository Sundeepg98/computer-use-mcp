#!/usr/bin/env python3
"""Verify that pip tests actually run"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the test module
from tests import test_package_tdd

# Create test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Load all tests
suite.addTests(loader.loadTestsFromModule(test_package_tdd))

# Run tests with verbose output
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Print specific pip test results
print("\n=== PIP TEST VERIFICATION ===")
for test in result.testsRun:
    print(f"Test #{test}")

# Check if pip tests were included
test_names = [test._testMethodName for test in suite]
pip_tests = [name for name in test_names if 'pip' in name or 'requirements' in name]

print(f"\nPip-related tests found: {len(pip_tests)}")
for test in pip_tests:
    print(f"  - {test}")

print(f"\nTotal tests run: {result.testsRun}")
print(f"Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
print(f"Success: {result.wasSuccessful()}")