#!/bin/bash

# Run tests and pipe output properly
echo "=== Running TDD Tests with Proper Piping ==="

# Get test count
echo -n "Total tests: "
python3 tests/test_package_tdd.py -v 2>&1 | grep -c "^test_"

# Get pass count
echo -n "Passed tests: "
python3 tests/test_package_tdd.py -v 2>&1 | grep " \.\.\. ok$" | wc -l

# Get fail count
echo -n "Failed tests: "
python3 tests/test_package_tdd.py -v 2>&1 | grep " \.\.\. FAIL$" | wc -l

# Get error count
echo -n "Error tests: "
python3 tests/test_package_tdd.py -v 2>&1 | grep " \.\.\. ERROR$" | wc -l

# Show summary line
echo -e "\n=== Summary ==="
python3 tests/test_package_tdd.py 2>&1 | grep "^Ran " | head -1
python3 tests/test_package_tdd.py 2>&1 | grep "^OK\|^FAILED" | head -1

# List all test names
echo -e "\n=== All Test Names ==="
python3 tests/test_package_tdd.py -v 2>&1 | grep "^test_" | awk '{print $1}' | sort

# Show test categories
echo -e "\n=== Test Categories ==="
python3 tests/test_package_tdd.py -v 2>&1 | grep "^test_" | awk -F'_' '{print $2}' | sort -u

# Final status
echo -e "\n=== Final Status ==="
if python3 tests/test_package_tdd.py 2>&1 | grep -q "^OK$"; then
    echo "✅ ALL TESTS PASS - 100% SUCCESS"
else
    echo "❌ SOME TESTS FAILED"
    python3 tests/test_package_tdd.py 2>&1 | grep "^FAILED"
fi