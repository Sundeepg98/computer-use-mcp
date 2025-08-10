#!/usr/bin/env python3
"""Analyze security test results and create fix plan"""
import re
import json
from datetime import datetime

def analyze_results(file_path='security_test_results.txt'):
    """Parse and analyze security test results"""
    print("🔒 SECURITY TEST ANALYSIS")
    print("━" * 60)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract test results
    passed_tests = re.findall(r'test_\w+.*?PASSED', content)
    failed_tests = re.findall(r'(test_\w+).*?FAILED', content)
    
    # Extract failure details
    failures = {}
    failure_blocks = re.split(r'_{10,}', content)
    
    for block in failure_blocks:
        if 'FAILED' in block:
            test_match = re.search(r'(test_\w+)', block)
            if test_match:
                test_name = test_match.group(1)
                # Extract assertion errors
                assertion_match = re.search(r'AssertionError: (.+?)(?:\n|$)', block)
                error_match = re.search(r'E\s+(.+?)(?:\n|$)', block)
                
                failures[test_name] = {
                    'assertion': assertion_match.group(1) if assertion_match else None,
                    'error': error_match.group(1) if error_match else None,
                    'block': block[:500]  # First 500 chars
                }
    
    # Summary
    total_tests = len(passed_tests) + len(failed_tests)
    pass_rate = len(passed_tests) / total_tests * 100 if total_tests > 0 else 0
    
    print(f"\n📊 Test Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {len(passed_tests)} ({pass_rate:.1f}%)")
    print(f"  Failed: {len(failed_tests)} ({100-pass_rate:.1f}%)")
    
    # Categorize failures
    security_categories = {
        'injection': [],
        'permission': [],
        'validation': [],
        'authentication': [],
        'other': []
    }
    
    for test_name, details in failures.items():
        if 'injection' in test_name or 'sql' in test_name or 'xss' in test_name:
            security_categories['injection'].append(test_name)
        elif 'permission' in test_name or 'auth' in test_name or 'access' in test_name:
            security_categories['permission'].append(test_name)
        elif 'valid' in test_name or 'sanitiz' in test_name:
            security_categories['validation'].append(test_name)
        elif 'token' in test_name or 'session' in test_name:
            security_categories['authentication'].append(test_name)
        else:
            security_categories['other'].append(test_name)
    
    print("\n🔍 Failure Categories:")
    for category, tests in security_categories.items():
        if tests:
            print(f"\n  {category.upper()} ({len(tests)} failures):")
            for test in tests[:5]:  # Show first 5
                print(f"    - {test}")
                if failures.get(test, {}).get('assertion'):
                    print(f"      → {failures[test]['assertion'][:80]}...")
    
    # Generate fix recommendations
    print("\n💡 Fix Recommendations:")
    
    recommendations = []
    
    if security_categories['injection']:
        recommendations.append({
            'priority': 'CRITICAL',
            'category': 'Injection Protection',
            'action': 'Implement input sanitization and parameterized queries',
            'tests': len(security_categories['injection'])
        })
    
    if security_categories['permission']:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Permission Controls',
            'action': 'Add proper authorization checks and privilege validation',
            'tests': len(security_categories['permission'])
        })
    
    if security_categories['validation']:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Input Validation',
            'action': 'Add comprehensive input validation and sanitization',
            'tests': len(security_categories['validation'])
        })
    
    for rec in sorted(recommendations, key=lambda x: x['priority']):
        print(f"\n  [{rec['priority']}] {rec['category']}:")
        print(f"    Action: {rec['action']}")
        print(f"    Affects: {rec['tests']} tests")
    
    # Save analysis
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total_tests,
            'passed': len(passed_tests),
            'failed': len(failed_tests),
            'pass_rate': pass_rate
        },
        'categories': {k: len(v) for k, v in security_categories.items()},
        'recommendations': recommendations,
        'failures': failures
    }
    
    with open('security_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Analysis saved to security_analysis_report.json")
    
    return report

if __name__ == "__main__":
    analyze_results()