#!/bin/bash

echo "Testing package after removing ultrathink branding..."
echo "============================================"

# Run tests and capture results
python3 tests/test_package_tdd.py > test_results.txt 2>&1
RESULT=$?

# Show summary
echo -n "Tests run: "
grep "^Ran " test_results.txt | awk '{print $2}'

echo -n "Status: "
if grep -q "^OK$" test_results.txt; then
    echo "✅ ALL TESTS PASS"
else
    echo "❌ SOME TESTS FAILED"
    grep "^FAILED" test_results.txt
fi

# Check specific tests
echo ""
echo "Visual Analysis Tests:"
grep -E "test_.*visual|test_.*analyzer" test_results.txt | head -3

rm test_results.txt

exit $RESULT