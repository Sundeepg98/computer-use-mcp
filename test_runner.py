#!/usr/bin/env python3
"""Test runner that properly handles output for piping"""

import subprocess
import sys

# Run the tests
result = subprocess.run(
    [sys.executable, 'tests/test_package_tdd.py', '-v'],
    capture_output=True,
    text=True
)

# Output everything to stdout (merge stderr)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Exit with same code
sys.exit(result.returncode)