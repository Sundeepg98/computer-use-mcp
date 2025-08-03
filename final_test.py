#!/usr/bin/env python3
"""Final test after refactoring"""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, 'tests/test_package_tdd.py'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

# Extract summary
lines = result.stdout.split('\n')
for line in lines[-5:]:
    if line.strip():
        print(line)

sys.exit(result.returncode)