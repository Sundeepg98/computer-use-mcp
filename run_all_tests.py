#!/usr/bin/env python3
"""
Run all tests and provide comprehensive report
Shows what's actually working vs what needs fixing
"""

import unittest
import sys
import os
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def run_test_suite(test_file, test_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print('='*60)
    
    # Dynamically import the test module
    test_module = __import__(f'tests.{test_file.stem}', fromlist=[''])
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        'name': test_name,
        'total': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'result': result
    }


def main():
    """Run all test suites and provide summary"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT - ULTRATHINK ANALYSIS")
    print("="*80)
    
    # Test files to run in order
    test_suites = [
        ('test_package_tdd.py', 'Package Structure Tests (Original 36)'),
        ('test_computer_use_core.py', 'Functional Tests (NEW)'),
        ('test_integration.py', 'Integration Tests (NEW)'),
        ('test_e2e.py', 'End-to-End Tests (NEW)'),
        ('test_safety.py', 'Safety Tests'),
        ('test_mcp_protocol.py', 'MCP Protocol Tests'),
        ('test_visual.py', 'Visual Analyzer Tests'),
    ]
    
    results = []
    start_time = time.time()
    
    # Run each test suite
    for test_file, test_name in test_suites:
        test_path = Path('tests') / test_file
        if test_path.exists():
            try:
                result = run_test_suite(test_path, test_name)
                results.append(result)
            except Exception as e:
                print(f"\nERROR running {test_name}: {e}")
                results.append({
                    'name': test_name,
                    'total': 0,
                    'failures': 0,
                    'errors': 1,
                    'success': False,
                    'error_msg': str(e)
                })
        else:
            print(f"\nSKIPPING {test_name} - file not found")
    
    # Calculate totals
    total_tests = sum(r['total'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_passed = total_tests - total_failures - total_errors
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL SUMMARY - THE TRUTH")
    print("="*80)
    
    print("\nDetailed Results:")
    print("-"*80)
    print(f"{'Test Suite':<40} {'Tests':>8} {'Pass':>8} {'Fail':>8} {'Error':>8}")
    print("-"*80)
    
    for result in results:
        passed = result['total'] - result['failures'] - result['errors']
        print(f"{result['name']:<40} {result['total']:>8} {passed:>8} {result['failures']:>8} {result['errors']:>8}")
    
    print("-"*80)
    print(f"{'TOTAL':<40} {total_tests:>8} {total_passed:>8} {total_failures:>8} {total_errors:>8}")
    
    # Calculate percentages
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        functional_tests = sum(r['total'] for r in results if 'NEW' in r['name'])
        functional_passed = sum(r['total'] - r['failures'] - r['errors'] 
                              for r in results if 'NEW' in r['name'])
        
        print(f"\nOverall Pass Rate: {pass_rate:.1f}%")
        print(f"Original 36 Structure Tests: {results[0]['total'] - results[0]['failures'] - results[0]['errors']}/{results[0]['total']}")
        print(f"New Functional Tests: {functional_passed}/{functional_tests}")
    
    # Execution time
    elapsed = time.time() - start_time
    print(f"\nTotal execution time: {elapsed:.2f} seconds")
    
    # The Verdict
    print("\n" + "="*80)
    print("ULTRATHINK VERDICT")
    print("="*80)
    
    if total_errors > 0:
        print("\n❌ CRITICAL: Tests have errors - code is broken")
        print("   These aren't just failures, but actual crashes/exceptions")
    elif total_failures > 0:
        print("\n❌ FAILING: Tests are failing - functionality not working as expected")
        print("   The code runs but doesn't do what it should")
    elif functional_tests == 0:
        print("\n⚠️  WARNING: No functional tests found!")
        print("   We only tested structure, not actual functionality")
    elif pass_rate == 100:
        print("\n✅ SUCCESS: All tests pass!")
        print("   Package is ready for production")
    else:
        print(f"\n⚠️  PARTIAL: {pass_rate:.1f}% tests passing")
        print("   More work needed before production")
    
    # Return exit code
    return 0 if total_failures == 0 and total_errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())