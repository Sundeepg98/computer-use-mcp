#!/usr/bin/env python3
"""
Comprehensive Test Runner for computer-use-mcp
Runs all test suites: unit, integration, e2e, safety, and stress tests
"""

import sys
import os
import time
import unittest
import json
from pathlib import Path
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Test suite categories
TEST_SUITES = {
    "Unit Tests": [
        "test_computer_use_core",
        "test_xserver_manager", 
        "test_xserver_integration",
        "test_mcp_protocol"
    ],
    "Integration Tests": [
        "test_integration_comprehensive"
    ],
    "End-to-End Tests": [
        "test_e2e_workflows"
    ],
    "Safety & Security Tests": [
        "test_safety_security"
    ],
    "Stress & Reliability Tests": [
        "test_stress_reliability"
    ]
}


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🎯 COMPREHENSIVE TEST SUITE EXECUTION")
        print("=====================================")
        print()
        
        self.start_time = time.time()
        
        for suite_name, test_modules in TEST_SUITES.items():
            print(f"📋 {suite_name}")
            print("-" * (len(suite_name) + 3))
            
            suite_results = self._run_test_suite(test_modules)
            self.results[suite_name] = suite_results
            
            self._print_suite_summary(suite_name, suite_results)
            print()
        
        self.end_time = time.time()
        self._print_comprehensive_summary()
    
    def _run_test_suite(self, test_modules):
        """Run a specific test suite"""
        suite_results = {
            "modules": {},
            "total_tests": 0,
            "total_failures": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "success_rate": 0,
            "duration": 0
        }
        
        suite_start = time.time()
        
        for module_name in test_modules:
            module_result = self._run_test_module(module_name)
            suite_results["modules"][module_name] = module_result
            
            suite_results["total_tests"] += module_result["tests_run"]
            suite_results["total_failures"] += module_result["failures"]
            suite_results["total_errors"] += module_result["errors"]
            suite_results["total_skipped"] += module_result["skipped"]
        
        suite_end = time.time()
        suite_results["duration"] = suite_end - suite_start
        
        # Calculate success rate
        if suite_results["total_tests"] > 0:
            successful = (suite_results["total_tests"] - 
                         suite_results["total_failures"] - 
                         suite_results["total_errors"])
            suite_results["success_rate"] = (successful / suite_results["total_tests"]) * 100
        
        return suite_results
    
    def _run_test_module(self, module_name):
        """Run a specific test module"""
        try:
            # Import the test module
            module = __import__(module_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Capture output
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream, 
                verbosity=0,
                buffer=True
            )
            
            # Run tests
            module_start = time.time()
            result = runner.run(suite)
            module_end = time.time()
            
            return {
                "status": "success",
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
                "duration": module_end - module_start,
                "output": stream.getvalue()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
                "skipped": 0,
                "duration": 0,
                "error_message": str(e)
            }
    
    def _print_suite_summary(self, suite_name, suite_results):
        """Print summary for a test suite"""
        if suite_results["total_tests"] == 0:
            print("  ❌ No tests found or failed to load")
            return
        
        success_rate = suite_results["success_rate"]
        
        if success_rate == 100.0:
            status_icon = "✅"
        elif success_rate >= 90.0:
            status_icon = "⚠️"
        else:
            status_icon = "❌"
        
        print(f"  {status_icon} {suite_results['total_tests']} tests, "
              f"{success_rate:.1f}% success, "
              f"{suite_results['duration']:.2f}s")
        
        if suite_results["total_failures"] > 0:
            print(f"    - {suite_results['total_failures']} failures")
        
        if suite_results["total_errors"] > 0:
            print(f"    - {suite_results['total_errors']} errors")
        
        # Show module breakdown
        for module_name, module_result in suite_results["modules"].items():
            if module_result["status"] == "error":
                print(f"    ❌ {module_name}: Failed to load - {module_result.get('error_message', 'Unknown error')}")
            else:
                module_success_rate = 0
                if module_result["tests_run"] > 0:
                    successful = (module_result["tests_run"] - 
                                 module_result["failures"] - 
                                 module_result["errors"])
                    module_success_rate = (successful / module_result["tests_run"]) * 100
                
                if module_success_rate == 100.0:
                    print(f"      ✅ {module_name}: {module_result['tests_run']} tests")
                else:
                    print(f"      ⚠️  {module_name}: {module_result['tests_run']} tests, "
                          f"{module_success_rate:.1f}% success")
    
    def _print_comprehensive_summary(self):
        """Print comprehensive summary of all tests"""
        total_duration = self.end_time - self.start_time
        
        print("🎯 COMPREHENSIVE TEST RESULTS")
        print("=============================")
        print()
        
        # Calculate overall statistics
        total_tests = sum(suite["total_tests"] for suite in self.results.values())
        total_failures = sum(suite["total_failures"] for suite in self.results.values())
        total_errors = sum(suite["total_errors"] for suite in self.results.values())
        total_skipped = sum(suite["total_skipped"] for suite in self.results.values())
        
        overall_success_rate = 0
        if total_tests > 0:
            successful = total_tests - total_failures - total_errors
            overall_success_rate = (successful / total_tests) * 100
        
        # Print summary table
        print(f"Total Tests:      {total_tests}")
        print(f"Successful:       {total_tests - total_failures - total_errors}")
        print(f"Failures:         {total_failures}")
        print(f"Errors:           {total_errors}")
        print(f"Skipped:          {total_skipped}")
        print(f"Success Rate:     {overall_success_rate:.1f}%")
        print(f"Total Duration:   {total_duration:.2f}s")
        print()
        
        # Suite breakdown
        print("📊 Suite Breakdown:")
        for suite_name, suite_result in self.results.items():
            success_rate = suite_result["success_rate"]
            
            if success_rate == 100.0:
                status = "✅ PASS"
            elif success_rate >= 90.0:
                status = "⚠️  WARN"
            else:
                status = "❌ FAIL"
            
            print(f"  {status} {suite_name}: "
                  f"{suite_result['total_tests']} tests, "
                  f"{success_rate:.1f}% success")
        
        print()
        
        # Overall assessment
        if overall_success_rate == 100.0:
            print("🎉 PERFECT SCORE - ALL TESTS PASSED!")
            print("🚀 System is production-ready with comprehensive coverage!")
        elif overall_success_rate >= 95.0:
            print("🎯 EXCELLENT - High success rate achieved!")
            print("✅ System demonstrates strong reliability and security!")
        elif overall_success_rate >= 90.0:
            print("⚠️  GOOD - Mostly successful with some issues to address")
            print("🔧 Review failures and improve before production deployment")
        else:
            print("❌ NEEDS WORK - Significant issues detected")
            print("🚨 Address failures before deployment")
        
        print()
        print("📋 Test Coverage Areas:")
        print("  ✅ Unit Testing - Individual component functionality")
        print("  ✅ Integration Testing - Component interactions")
        print("  ✅ End-to-End Testing - Complete workflows")
        print("  ✅ Safety & Security Testing - Protection mechanisms")
        print("  ✅ Stress & Reliability Testing - Performance under load")
        
        # Save results to file
        self._save_results()
    
    def _save_results(self):
        """Save test results to JSON file"""
        results_data = {
            "timestamp": time.time(),
            "duration": self.end_time - self.start_time,
            "summary": {
                "total_tests": sum(suite["total_tests"] for suite in self.results.values()),
                "total_failures": sum(suite["total_failures"] for suite in self.results.values()),
                "total_errors": sum(suite["total_errors"] for suite in self.results.values()),
                "total_skipped": sum(suite["total_skipped"] for suite in self.results.values()),
                "overall_success_rate": 0
            },
            "suites": self.results
        }
        
        # Calculate overall success rate
        total_tests = results_data["summary"]["total_tests"]
        if total_tests > 0:
            successful = (total_tests - 
                         results_data["summary"]["total_failures"] - 
                         results_data["summary"]["total_errors"])
            results_data["summary"]["overall_success_rate"] = (successful / total_tests) * 100
        
        # Save to file
        results_file = Path(__file__).parent / "comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")


def main():
    """Main test runner"""
    runner = ComprehensiveTestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()