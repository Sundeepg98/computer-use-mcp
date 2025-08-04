#!/usr/bin/env python3
"""
Comprehensive Stress and Reliability Tests for computer-use-mcp
Tests system behavior under load, concurrent usage, and edge conditions
"""

import sys
import os
import json
import time
import threading
import concurrent.futures
import random
import gc
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from mcp.mcp_server import ComputerUseServer
from mcp.computer_use_core import ComputerUseCore


class TestConcurrentUsageStress(unittest.TestCase):
    """Test system behavior under concurrent usage stress"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_concurrent_screenshot_requests(self):
        """Test handling multiple concurrent screenshot requests"""
        def take_screenshot(request_id):
            """Take a screenshot with unique ID"""
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"analyze": f"Concurrent test {request_id}"}
                }
            }
            
            start_time = time.time()
            response = self.server.handle_request(request)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "response": response,
                "duration": end_time - start_time
            }
        
        # Launch 20 concurrent screenshot requests
        num_requests = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(take_screenshot, i) for i in range(num_requests)]
            results = [future.result(timeout=30) for future in futures]
        
        # Verify all requests completed successfully
        self.assertEqual(len(results), num_requests)
        
        for result in results:
            self.assertIn("result", result["response"])
            self.assertEqual(result["response"]["id"], result["request_id"])
            self.assertLess(result["duration"], 10.0)  # Should complete within 10 seconds
        
        # Verify response times are reasonable
        durations = [r["duration"] for r in results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        self.assertLess(avg_duration, 2.0)  # Average should be under 2 seconds
        self.assertLess(max_duration, 10.0)  # Max should be under 10 seconds
    
    def test_concurrent_mixed_operations(self):
        """Test handling mixed concurrent operations"""
        def random_operation(request_id):
            """Perform a random operation"""
            operations = [
                ("screenshot", {"analyze": f"Test {request_id}"}),
                ("click", {"x": random.randint(10, 1000), "y": random.randint(10, 1000)}),
                ("type", {"text": f"Test message {request_id}"}),
                ("key", {"key": "Return"}),
                ("scroll", {"direction": random.choice(["up", "down"]), "amount": random.randint(1, 5)}),
                ("wait", {"seconds": random.uniform(0.01, 0.1)}),
            ]
            
            tool_name, args = random.choice(operations)
            
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            start_time = time.time()
            response = self.server.handle_request(request)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "operation": tool_name,
                "response": response,
                "duration": end_time - start_time
            }
        
        # Launch 50 concurrent mixed operations
        num_requests = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(random_operation, i) for i in range(num_requests)]
            results = [future.result(timeout=30) for future in futures]
        
        # Verify all requests completed
        self.assertEqual(len(results), num_requests)
        
        # Analyze results by operation type
        operation_stats = {}
        for result in results:
            op = result["operation"]
            if op not in operation_stats:
                operation_stats[op] = {"count": 0, "durations": [], "successes": 0}
            
            operation_stats[op]["count"] += 1
            operation_stats[op]["durations"].append(result["duration"])
            
            if "result" in result["response"]:
                operation_stats[op]["successes"] += 1
        
        # Verify reasonable performance for each operation type
        for op, stats in operation_stats.items():
            if stats["count"] > 0:
                success_rate = stats["successes"] / stats["count"]
                avg_duration = sum(stats["durations"]) / len(stats["durations"])
                
                self.assertGreater(success_rate, 0.8, f"Low success rate for {op}: {success_rate}")
                self.assertLess(avg_duration, 5.0, f"Slow performance for {op}: {avg_duration}s")
    
    def test_rapid_sequential_requests(self):
        """Test handling rapid sequential requests"""
        operations = [
            ("screenshot", {}),
            ("click", {"x": 100, "y": 100}),
            ("type", {"text": "rapid test"}),
            ("key", {"key": "Return"}),
            ("wait", {"seconds": 0.01}),
        ] * 20  # 100 total operations
        
        start_time = time.time()
        responses = []
        
        for i, (tool_name, args) in enumerate(operations):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            response = self.server.handle_request(request)
            responses.append(response)
            
            # Brief pause to avoid overwhelming
            time.sleep(0.001)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verify all requests completed
        self.assertEqual(len(responses), len(operations))
        
        # Verify reasonable total time
        self.assertLess(total_duration, 30.0)  # Should complete within 30 seconds
        
        # Verify all responses are valid
        for i, response in enumerate(responses):
            self.assertTrue("result" in response or "error" in response)
            self.assertEqual(response["id"], i)
    
    def test_long_running_session_stability(self):
        """Test stability over a long-running session"""
        session_duration = 10  # 10 seconds of continuous operation
        start_time = time.time()
        operation_count = 0
        errors = []
        
        while time.time() - start_time < session_duration:
            # Perform a random operation
            operations = [
                ("screenshot", {"analyze": f"Long session {operation_count}"}),
                ("click", {"x": random.randint(50, 500), "y": random.randint(50, 500)}),
                ("type", {"text": f"Session test {operation_count}"}),
                ("wait", {"seconds": 0.05}),
            ]
            
            tool_name, args = random.choice(operations)
            
            request = {
                "jsonrpc": "2.0",
                "id": operation_count,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            try:
                response = self.server.handle_request(request)
                
                if "error" in response:
                    errors.append((operation_count, tool_name, response["error"]))
                
                operation_count += 1
                
                # Brief pause
                time.sleep(0.01)
                
            except Exception as e:
                errors.append((operation_count, tool_name, str(e)))
                break
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Verify session stability
        self.assertGreater(operation_count, 50)  # Should complete many operations
        self.assertLess(len(errors), operation_count * 0.1)  # Error rate < 10%
        self.assertGreaterEqual(actual_duration, session_duration * 0.9)  # Ran for expected time


class TestMemoryAndResourceStress(unittest.TestCase):
    """Test memory usage and resource management under stress"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable under load"""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Perform many operations
        for i in range(200):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"analyze": f"Memory test {i}"}
                }
            }
            
            response = self.server.handle_request(request)
            self.assertIn("result", response)
            
            # Force garbage collection periodically
            if i % 50 == 0:
                gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        max_increase = 50 * 1024 * 1024  # 50MB
        self.assertLess(memory_increase, max_increase, 
                       f"Memory increased by {memory_increase / (1024*1024):.1f}MB")
    
    def test_large_response_handling(self):
        """Test handling of large responses"""
        # Generate requests that might produce large responses
        large_requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"analyze": "A" * 1000}  # Large analysis request
                }
            },
            {
                "jsonrpc": "2.0", 
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": "B" * 5000}  # Large text input
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list"  # List all tools (potentially large)
            },
        ]
        
        for request in large_requests:
            with self.subTest(request_id=request["id"]):
                start_time = time.time()
                response = self.server.handle_request(request)
                end_time = time.time()
                
                # Should handle large requests within reasonable time
                self.assertLess(end_time - start_time, 10.0)
                
                # Should get valid response
                self.assertTrue("result" in response or "error" in response)
                self.assertEqual(response["id"], request["id"])
    
    def test_garbage_collection_behavior(self):
        """Test garbage collection behavior under load"""
        import gc
        
        gc.collect()  # Clean start
        initial_objects = len(gc.get_objects())
        
        # Perform many operations that create objects
        for i in range(100):
            # Create various request types
            requests = [
                {
                    "jsonrpc": "2.0",
                    "id": f"{i}-1",
                    "method": "tools/call",
                    "params": {
                        "name": "screenshot",
                        "arguments": {"analyze": f"GC test {i}"}
                    }
                },
                {
                    "jsonrpc": "2.0",
                    "id": f"{i}-2", 
                    "method": "tools/call",
                    "params": {
                        "name": "type",
                        "arguments": {"text": f"GC test data {i}"}
                    }
                }
            ]
            
            for request in requests:
                response = self.server.handle_request(request)
                self.assertTrue("result" in response or "error" in response)
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count should not grow excessively
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 1000, f"Object count grew by {object_growth}")


class TestErrorRecoveryStress(unittest.TestCase):
    """Test error recovery and resilience under stress"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_error_recovery_after_failures(self):
        """Test system recovery after encountering errors"""
        # Mix of valid and invalid requests
        requests = [
            # Valid requests
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", 
             "params": {"name": "screenshot", "arguments": {}}},
            
            # Invalid requests that should cause errors
            {"jsonrpc": "2.0", "id": 3, "method": "invalid/method"},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "invalid_tool", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "click", "arguments": {"x": "invalid"}}},
             
            # More valid requests (should work after errors)
            {"jsonrpc": "2.0", "id": 6, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
             "params": {"name": "wait", "arguments": {"seconds": 0.01}}},
        ]
        
        responses = []
        for request in requests:
            response = self.server.handle_request(request)
            responses.append(response)
        
        # Verify all requests got responses
        self.assertEqual(len(responses), len(requests))
        
        # Verify valid requests succeeded even after errors
        self.assertIn("result", responses[0])  # tools/list
        self.assertIn("result", responses[1])  # screenshot
        self.assertIn("error", responses[2])   # invalid method
        self.assertIn("error", responses[3])   # invalid tool
        self.assertIn("error", responses[4])   # invalid args
        self.assertIn("result", responses[5])  # tools/list after errors
        self.assertIn("result", responses[6])  # wait after errors
    
    def test_malformed_request_resilience(self):
        """Test resilience against malformed requests"""
        malformed_requests = [
            # Missing required fields
            {"id": 1, "method": "tools/list"},  # Missing jsonrpc
            {"jsonrpc": "2.0", "method": "tools/list"},  # Missing id
            {"jsonrpc": "2.0", "id": 1},  # Missing method
            
            # Invalid field values
            {"jsonrpc": "1.0", "id": 1, "method": "tools/list"},  # Wrong version
            {"jsonrpc": "2.0", "id": None, "method": "tools/list"},  # Null id
            {"jsonrpc": "2.0", "id": 1, "method": None},  # Null method
            
            # Invalid structure
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call"},  # Missing params
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": None},  # Null params
        ]
        
        valid_request = {"jsonrpc": "2.0", "id": 999, "method": "tools/list"}
        
        for i, malformed in enumerate(malformed_requests):
            with self.subTest(request_index=i):
                # Send malformed request
                response = self.server.handle_request(malformed)
                
                # Should get error or None (for notifications)
                if response is not None:
                    self.assertIn("error", response)
                
                # System should still work after malformed request
                valid_response = self.server.handle_request(valid_request)
                self.assertIn("result", valid_response)
                self.assertEqual(valid_response["id"], 999)
    
    def test_exception_handling_stress(self):
        """Test exception handling under various stress conditions"""
        # Operations that might cause different types of exceptions
        stress_operations = [
            # Type errors
            {"name": "click", "arguments": {"x": None, "y": 100}},
            {"name": "type", "arguments": {"text": None}},
            
            # Value errors  
            {"name": "wait", "arguments": {"seconds": "invalid"}},
            {"name": "scroll", "arguments": {"direction": "invalid", "amount": -1}},
            
            # Missing arguments
            {"name": "click", "arguments": {}},
            {"name": "drag", "arguments": {"start_x": 10}},  # Missing other coords
        ]
        
        for i, operation in enumerate(stress_operations):
            with self.subTest(operation_index=i):
                request = {
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": "tools/call",
                    "params": operation
                }
                
                # Should handle exception gracefully
                response = self.server.handle_request(request)
                
                # Should get error response, not crash
                self.assertIn("error", response)
                self.assertEqual(response["id"], i)
                
                # System should remain functional
                test_request = {
                    "jsonrpc": "2.0",
                    "id": 9999,
                    "method": "tools/list"
                }
                test_response = self.server.handle_request(test_request)
                self.assertIn("result", test_response)


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks and regression tests"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_response_time_benchmarks(self):
        """Test response time benchmarks for different operations"""
        benchmark_operations = {
            "tools/list": {},
            "screenshot": {"analyze": "benchmark test"},
            "click": {"x": 100, "y": 100},
            "type": {"text": "benchmark text"},
            "key": {"key": "Return"},
            "wait": {"seconds": 0.01},
        }
        
        benchmark_results = {}
        
        for operation_name, args in benchmark_operations.items():
            times = []
            
            # Run each operation 10 times
            for _ in range(10):
                if operation_name == "tools/list":
                    request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    }
                else:
                    request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": operation_name,
                            "arguments": args
                        }
                    }
                
                start_time = time.time()
                response = self.server.handle_request(request)
                end_time = time.time()
                
                self.assertTrue("result" in response or "error" in response)
                times.append(end_time - start_time)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            benchmark_results[operation_name] = {
                "avg": avg_time,
                "max": max_time,
                "min": min_time,
                "samples": len(times)
            }
        
        # Verify performance benchmarks
        for operation, stats in benchmark_results.items():
            with self.subTest(operation=operation):
                # Average response time should be reasonable
                self.assertLess(stats["avg"], 1.0, 
                               f"{operation} avg time too high: {stats['avg']:.3f}s")
                
                # Max response time should not be excessive
                self.assertLess(stats["max"], 3.0,
                               f"{operation} max time too high: {stats['max']:.3f}s")
                
                # Variance should not be too high (consistency)
                variance = stats["max"] - stats["min"]
                self.assertLess(variance, 2.0,
                               f"{operation} response time variance too high: {variance:.3f}s")
    
    def test_throughput_benchmark(self):
        """Test request throughput benchmark"""
        num_requests = 100
        start_time = time.time()
        
        successful_requests = 0
        
        for i in range(num_requests):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "wait",
                    "arguments": {"seconds": 0.001}
                }
            }
            
            response = self.server.handle_request(request)
            
            if "result" in response:
                successful_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput metrics
        requests_per_second = successful_requests / total_time
        avg_request_time = total_time / successful_requests if successful_requests > 0 else float('inf')
        
        # Verify throughput benchmarks
        self.assertGreater(requests_per_second, 20, 
                          f"Throughput too low: {requests_per_second:.1f} req/s")
        self.assertLess(avg_request_time, 0.1,
                       f"Average request time too high: {avg_request_time:.3f}s")
        self.assertGreater(successful_requests, num_requests * 0.95,
                          f"Success rate too low: {successful_requests}/{num_requests}")
    
    def test_concurrent_throughput_benchmark(self):
        """Test concurrent request throughput"""
        def worker_thread(thread_id, requests_per_thread):
            """Worker thread that sends multiple requests"""
            successful = 0
            start_time = time.time()
            
            for i in range(requests_per_thread):
                request = {
                    "jsonrpc": "2.0",
                    "id": f"{thread_id}-{i}",
                    "method": "tools/call",
                    "params": {
                        "name": "wait",
                        "arguments": {"seconds": 0.001}
                    }
                }
                
                response = self.server.handle_request(request)
                if "result" in response:
                    successful += 1
            
            end_time = time.time()
            return {
                "thread_id": thread_id,
                "successful": successful,
                "duration": end_time - start_time
            }
        
        # Run 5 threads with 20 requests each
        num_threads = 5
        requests_per_thread = 20
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(worker_thread, i, requests_per_thread) 
                for i in range(num_threads)
            ]
            results = [future.result(timeout=30) for future in futures]
        
        # Analyze concurrent performance
        total_successful = sum(r["successful"] for r in results)
        total_requests = num_threads * requests_per_thread
        max_duration = max(r["duration"] for r in results)
        
        concurrent_throughput = total_successful / max_duration if max_duration > 0 else 0
        success_rate = total_successful / total_requests
        
        # Verify concurrent performance
        self.assertGreater(concurrent_throughput, 50,
                          f"Concurrent throughput too low: {concurrent_throughput:.1f} req/s")
        self.assertGreater(success_rate, 0.95,
                          f"Concurrent success rate too low: {success_rate:.2f}")
        self.assertLess(max_duration, 10.0,
                       f"Concurrent execution too slow: {max_duration:.2f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)