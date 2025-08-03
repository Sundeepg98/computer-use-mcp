#!/usr/bin/env python3
"""
Verify TDD implementation for computer-use-mcp
Shows which tests pass/fail after implementation
"""

import unittest
import sys
from pathlib import Path

# Import test modules
sys.path.insert(0, str(Path(__file__).parent / 'tests'))
from test_package_tdd import *


def run_tdd_verification():
    """Run all TDD tests and show results"""
    print("=" * 70)
    print("TDD VERIFICATION - Computer Use MCP Package")
    print("=" * 70)
    print("\nRunning all TDD tests to verify implementation...\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPackageStructure,
        TestPackageMetadata,
        TestCLIFunctionality,
        TestDockerIntegration,
        TestInstallation,
        TestExamples,
        TestMCPProtocolCompliance,
        TestSafetyAndSecurity,
        TestUltrathinkIntegration,
        TestContinuousIntegration,
        TestDocumentation,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("TDD VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_tests - failures - errors - skipped
    
    print(f"\nTotal Tests:  {total_tests}")
    print(f"✅ Passed:    {passed} ({passed/total_tests*100:.1f}%)")
    print(f"❌ Failed:    {failures}")
    print(f"🔥 Errors:    {errors}")
    print(f"⏭️  Skipped:   {skipped}")
    
    if failures > 0:
        print("\n" + "-" * 70)
        print("FAILED TESTS:")
        for test, traceback in result.failures[:5]:  # Show first 5 failures
            print(f"\n❌ {test}")
            print(f"   {traceback.split('AssertionError:')[1].strip()[:100] if 'AssertionError:' in traceback else 'See full output'}")
    
    if errors > 0:
        print("\n" + "-" * 70)
        print("ERROR TESTS:")
        for test, traceback in result.errors[:5]:  # Show first 5 errors
            print(f"\n🔥 {test}")
            print(f"   {traceback.split(':')[1].strip()[:100] if ':' in traceback else 'See full output'}")
    
    # Ultrathink analysis
    print("\n" + "=" * 70)
    print("ULTRATHINK TDD ANALYSIS")
    print("=" * 70)
    
    success_rate = passed / total_tests * 100
    
    if success_rate == 100:
        print("""
        🎉 PERFECT TDD IMPLEMENTATION!
        
        All tests pass, demonstrating:
        ✅ Complete package structure
        ✅ All configurations present
        ✅ Python modules implemented
        ✅ CLI fully functional
        ✅ Docker ready
        ✅ Safety validated
        ✅ MCP protocol compliant
        ✅ Documentation complete
        
        The package is production-ready!
        """)
    elif success_rate >= 90:
        print(f"""
        ✅ EXCELLENT TDD PROGRESS ({success_rate:.1f}%)
        
        Nearly complete implementation with minor gaps.
        Focus on remaining {failures + errors} issues.
        """)
    elif success_rate >= 70:
        print(f"""
        🔶 GOOD TDD PROGRESS ({success_rate:.1f}%)
        
        Core implementation complete, but significant work remains.
        Address {failures + errors} failing tests.
        """)
    else:
        print(f"""
        ⚠️  PARTIAL TDD IMPLEMENTATION ({success_rate:.1f}%)
        
        Many tests still failing. Continue implementing:
        - Missing components: {failures + errors} issues
        - Focus on critical path first
        """)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tdd_verification()
    sys.exit(0 if success else 1)