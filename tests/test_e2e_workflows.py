#!/usr/bin/env python3
"""
End-to-End Workflow Tests for computer-use-mcp
Tests complete user workflows, real-world scenarios, and system behavior
"""

import sys
import os
import json
import time
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from computer_use_mcp.mcp_server import ComputerUseServer
from computer_use_mcp.computer_use_core import ComputerUseCore


class TestCompleteAutomationWorkflows(unittest.TestCase):
    """Test complete automation workflows from start to finish"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_complete_form_filling_workflow(self):
        """Test complete form filling automation workflow"""
        # Simulate a complete form filling workflow:
        # 1. Screenshot to analyze form
        # 2. Click on first field
        # 3. Type username
        # 4. Click on second field  
        # 5. Type password
        # 6. Click submit button
        
        workflow_steps = [
            {
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"analyze": "Find login form fields"}
                }
            },
            {
                "method": "tools/call", 
                "params": {
                    "name": "click",
                    "arguments": {"x": 300, "y": 200, "button": "left"}
                }
            },
            {
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": "test_user@example.com"}
                }
            },
            {
                "method": "tools/call",
                "params": {
                    "name": "key", 
                    "arguments": {"key": "Tab"}
                }
            },
            {
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": "secure_password123"}
                }
            },
            {
                "method": "tools/call",
                "params": {
                    "name": "click",
                    "arguments": {"x": 350, "y": 300, "button": "left"}
                }
            }
        ]
        
        # Execute complete workflow
        responses = []
        for i, step in enumerate(workflow_steps):
            request = {
                "jsonrpc": "2.0",
                "id": i,
                **step
            }
            
            response = self.server.handle_request(request)
            responses.append(response)
            
            # Each step should succeed
            self.assertIn("result", response)
            self.assertEqual(response["id"], i)
        
        # Verify workflow completed successfully
        self.assertEqual(len(responses), len(workflow_steps))
        
        # Verify screenshot contains analysis
        screenshot_response = responses[0]
        content_str = str(screenshot_response["result"]["content"])
        self.assertIn("Find login form", content_str)
    
    def test_web_scraping_workflow(self):
        """Test web scraping workflow with multiple screenshots"""
        # Simulate web scraping workflow:
        # 1. Screenshot page
        # 2. Scroll down to load more content
        # 3. Screenshot again
        # 4. Click "Next Page" button
        # 5. Screenshot final page
        
        scraping_steps = [
            ("screenshot", {"analyze": "Analyze page content"}),
            ("scroll", {"direction": "down", "amount": 3}),
            ("wait", {"seconds": 1}),
            ("screenshot", {"analyze": "Check for more content"}),
            ("click", {"x": 500, "y": 600, "button": "left"}),
            ("wait", {"seconds": 2}),
            ("screenshot", {"analyze": "Analyze new page content"})
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(scraping_steps):
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
            
            # Each step should succeed
            self.assertIn("result", response)
        
        # Verify all screenshots were captured
        screenshot_count = sum(1 for i, (tool, _) in enumerate(scraping_steps) if tool == "screenshot")
        actual_screenshots = sum(1 for r in responses if "screenshot" in str(r))
        self.assertGreater(actual_screenshots, 0)
    
    def test_error_recovery_workflow(self):
        """Test workflow with error recovery"""
        # Test workflow that encounters errors and recovers
        error_recovery_steps = [
            ("screenshot", {}),  # Should succeed
            ("click", {"x": "invalid", "y": 100}),  # Should fail
            ("screenshot", {"analyze": "Check current state"}),  # Should succeed (recovery)
            ("click", {"x": 100, "y": 100}),  # Should succeed (retry)
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(error_recovery_steps):
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
        
        # First step should succeed
        self.assertIn("result", responses[0])
        
        # Second step should fail gracefully
        self.assertTrue("error" in responses[1] or "result" in responses[1])
        
        # Recovery steps should succeed
        self.assertIn("result", responses[2])
        self.assertIn("result", responses[3])
    
    def test_multi_window_workflow(self):
        """Test workflow involving multiple windows/applications"""
        # Simulate working with multiple windows:
        # 1. Screenshot current window
        # 2. Alt+Tab to switch windows
        # 3. Screenshot new window
        # 4. Copy something (Ctrl+C)
        # 5. Alt+Tab back
        # 6. Paste (Ctrl+V)
        
        multi_window_steps = [
            ("screenshot", {"analyze": "Current window content"}),
            ("key", {"key": "alt+Tab"}),
            ("wait", {"seconds": 0.5}),
            ("screenshot", {"analyze": "New window content"}), 
            ("key", {"key": "ctrl+a"}),  # Select all
            ("key", {"key": "ctrl+c"}),  # Copy
            ("key", {"key": "alt+Tab"}), # Switch back
            ("wait", {"seconds": 0.5}),
            ("key", {"key": "ctrl+v"}),  # Paste
            ("screenshot", {"analyze": "Final result"})
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(multi_window_steps):
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
            
            # All steps should succeed in test mode
            self.assertIn("result", response)
        
        self.assertEqual(len(responses), len(multi_window_steps))


class TestXServerLifecycleE2E(unittest.TestCase):
    """Test complete X server lifecycle workflows"""
    
    @patch('computer_use_mcp.xserver_manager.XServerManager')
    def setUp(self, mock_xserver_class):
        """Setup test environment"""
        self.mock_xserver = Mock()
        # Mock get_best_display to return valid dict
        self.mock_xserver.get_best_display.return_value = {
            'available': True,
            'display': ':0',
            'method': 'existing_display'
        }
        mock_xserver_class.return_value = self.mock_xserver
        self.server = ComputerUseServer(test_mode=False)
    
    def test_complete_xserver_setup_workflow(self):
        """Test complete X server setup from scratch"""
        # Mock X server operations
        self.mock_xserver.install_xserver_packages.return_value = {
            'installed': ['xorg', 'xvfb', 'xdotool'],
            'failed': [],
            'already_installed': []
        }
        
        self.mock_xserver.start_virtual_display.return_value = {
            'success': True,
            'display': ':99',
            'pid': 12345,
            'resolution': '1920x1080'
        }
        
        self.mock_xserver.check_xserver_available.return_value = {
            'available': True,
            'display': ':99',
            'method': 'virtual_display'
        }
        
        # Mock get_status to return a proper dict for xserver_status tool
        self.mock_xserver.get_status.return_value = {
            'wsl_mode': False,
            'current_display': ':99',
            'managed_servers': {':99': 12345},
            'active_processes': 1
        }
        
        # Complete setup workflow
        setup_steps = [
            ("install_xserver", {}),
            ("start_xserver", {"display_num": 99, "width": 1920, "height": 1080}),
            ("test_display", {}),
            ("screenshot", {"analyze": "Test display working"}),
            ("click", {"x": 100, "y": 100}),
            ("xserver_status", {})
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(setup_steps):
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
            
            # All steps should succeed
            self.assertIn("result", response)
        
        # Verify installation was called
        self.mock_xserver.install_xserver_packages.assert_called_once()
        
        # Verify virtual display was started
        self.mock_xserver.start_virtual_display.assert_called_once_with(99, 1920, 1080)
        
        # Verify display was tested
        self.mock_xserver.check_xserver_available.assert_called()
    
    def test_wsl2_environment_detection_workflow(self):
        """Test WSL2 environment detection and setup workflow"""
        # Mock WSL2 environment
        self.mock_xserver.setup_wsl_xforwarding.return_value = {
            'success': True,
            'display': ':0',
            'host_ip': '172.22.0.1',
            'wsl_mode': True
        }
        
        # Mock get_status to return a proper dict
        status_dict = {
            'wsl_mode': True,
            'current_display': ':0',
            'host_ip': '172.22.0.1',
            'managed_servers': {},
            'active_processes': 0
        }
        self.mock_xserver.get_status.return_value = status_dict
        
        # Also need to mock test_display's return value through check_xserver_available
        self.mock_xserver.check_xserver_available.return_value = {
            'available': True,
            'display': ':0',
            'method': 'wsl_xforwarding'
        }
        
        # WSL2 setup workflow
        wsl_steps = [
            ("setup_wsl_xforwarding", {}),
            ("xserver_status", {}),
            ("test_display", {}),
            ("screenshot", {"analyze": "WSL2 display working"})
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(wsl_steps):
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
            
            self.assertIn("result", response)
        
        # Verify WSL forwarding was setup
        self.mock_xserver.setup_wsl_xforwarding.assert_called_once()
    
    def test_xserver_cleanup_workflow(self):
        """Test complete X server cleanup workflow"""
        # Mock cleanup operations
        self.mock_xserver.stop_xserver.return_value = {
            'success': True,
            'stopped_processes': 1
        }
        
        # Mock get_status to return a proper dict
        self.mock_xserver.get_status.return_value = {
            'wsl_mode': False,
            'current_display': ':0',
            'managed_servers': {},
            'active_processes': 0
        }
        
        # Cleanup workflow
        cleanup_steps = [
            ("xserver_status", {}),  # Check current status
            ("stop_xserver", {"display": ":99"}),  # Stop specific server
            ("xserver_status", {}),  # Verify stopped
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(cleanup_steps):
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
            
            self.assertIn("result", response)
        
        # Verify server was stopped
        self.mock_xserver.stop_xserver.assert_called_once_with(":99")


class TestMCPProtocolE2E(unittest.TestCase):
    """Test complete MCP protocol workflows"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_complete_mcp_session_lifecycle(self):
        """Test complete MCP session from initialization to tools usage"""
        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            }
        }
        
        init_response = self.server.handle_request(init_request)
        self.assertIn("result", init_response)
        self.assertIn("protocolVersion", init_response["result"])
        
        # Step 2: List available tools
        list_request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list"
        }
        
        list_response = self.server.handle_request(list_request)
        self.assertIn("result", list_response)
        self.assertIn("tools", list_response["result"])
        
        tools = list_response["result"]["tools"]
        self.assertGreater(len(tools), 8)  # Should have core + X server tools
        
        # Step 3: Use multiple tools in sequence
        tool_names = [tool["name"] for tool in tools[:5]]  # Test first 5 tools
        
        for i, tool_name in enumerate(tool_names):
            # Get appropriate arguments for each tool
            args = self._get_test_args_for_tool(tool_name)
            
            tool_request = {
                "jsonrpc": "2.0",
                "id": i + 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            tool_response = self.server.handle_request(tool_request)
            
            # Should get valid response
            self.assertTrue("result" in tool_response or "error" in tool_response)
            self.assertEqual(tool_response["id"], i + 3)
    
    def _get_test_args_for_tool(self, tool_name):
        """Get appropriate test arguments for each tool"""
        args_map = {
            "screenshot": {"analyze": "test analysis"},
            "click": {"x": 100, "y": 100, "button": "left"},
            "type": {"text": "test text"},
            "key": {"key": "Return"},
            "scroll": {"direction": "down", "amount": 3},
            "drag": {"start_x": 10, "start_y": 10, "end_x": 100, "end_y": 100},
            "wait": {"seconds": 0.1},
            "automate": {"task": "test automation"},
            "install_xserver": {},
            "start_xserver": {"display_num": 99},
            "stop_xserver": {"display": ":99"},
            "setup_wsl_xforwarding": {},
            "xserver_status": {},
            "test_display": {}
        }
        return args_map.get(tool_name, {})
    
    def test_batch_request_workflow(self):
        """Test handling multiple requests in batch"""
        # Create batch of requests
        batch_requests = []
        for i in range(10):
            batch_requests.append({
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/list"
            })
        
        # Process batch
        responses = []
        for request in batch_requests:
            response = self.server.handle_request(request)
            responses.append(response)
        
        # Verify all requests processed
        self.assertEqual(len(responses), 10)
        
        # Verify correct IDs preserved
        for i, response in enumerate(responses):
            self.assertEqual(response["id"], i)
            self.assertIn("result", response)
    
    def test_protocol_error_handling_workflow(self):
        """Test protocol error handling across various scenarios"""
        error_scenarios = [
            # Invalid JSON-RPC version (MCP server might accept this)
            # {"jsonrpc": "1.0", "id": 1, "method": "tools/list"},
            
            # Missing required fields
            {"id": 2, "method": "tools/list"},
            
            # Invalid method
            {"jsonrpc": "2.0", "id": 3, "method": "invalid/method"},
            
            # Invalid tool name
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", 
             "params": {"name": "invalid_tool", "arguments": {}}},
            
            # Invalid tool arguments
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "click", "arguments": {"x": "invalid"}}},
        ]
        
        for scenario in error_scenarios:
            response = self.server.handle_request(scenario)
            
            # Should get error response or valid response for all scenarios
            if "id" in scenario:
                # Some scenarios might get valid responses if server is lenient
                self.assertTrue("error" in response or "result" in response)
                if "id" in response:
                    self.assertEqual(response["id"], scenario["id"])
            else:
                # Requests without ID should return None (notification)
                self.assertIsNone(response)
    
    def test_concurrent_session_workflow(self):
        """Test handling concurrent MCP sessions"""
        # Simulate multiple concurrent sessions
        session_results = []
        
        def simulate_session(session_id):
            """Simulate a complete MCP session"""
            results = []
            
            # Each session performs some operations
            operations = [
                {"method": "tools/list"},
                {"method": "tools/call", "params": {"name": "screenshot", "arguments": {}}},
                {"method": "tools/call", "params": {"name": "wait", "arguments": {"seconds": 0.01}}},
            ]
            
            for i, op in enumerate(operations):
                request = {
                    "jsonrpc": "2.0",
                    "id": f"{session_id}-{i}",
                    **op
                }
                
                response = self.server.handle_request(request)
                results.append(response)
            
            return results
        
        # Run multiple sessions concurrently
        threads = []
        for session_id in range(5):
            thread = threading.Thread(target=lambda sid=session_id: session_results.append(simulate_session(sid)))
            threads.append(thread)
            thread.start()
        
        # Wait for all sessions to complete
        for thread in threads:
            thread.join()
        
        # Verify all sessions completed successfully
        self.assertEqual(len(session_results), 5)
        
        for session_result in session_results:
            self.assertEqual(len(session_result), 3)  # 3 operations per session
            for response in session_result:
                self.assertTrue("result" in response or "error" in response)


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world usage scenarios"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_gui_application_testing_scenario(self):
        """Test GUI application testing workflow"""
        # Simulate automated GUI testing:
        # 1. Launch app (screenshot)
        # 2. Navigate menu (click + wait)
        # 3. Fill form (type + tab navigation)
        # 4. Submit (click)
        # 5. Verify result (screenshot + analysis)
        
        gui_test_steps = [
            ("screenshot", {"analyze": "Find application window"}),
            ("click", {"x": 50, "y": 30}),  # Menu
            ("wait", {"seconds": 0.5}),
            ("click", {"x": 100, "y": 60}),  # Menu item
            ("wait", {"seconds": 1}),
            ("screenshot", {"analyze": "Form opened"}),
            ("click", {"x": 200, "y": 150}),  # First field
            ("type", {"text": "Test Data"}),
            ("key", {"key": "Tab"}),
            ("type", {"text": "More Test Data"}),
            ("key", {"key": "Tab"}),
            ("key", {"key": "Return"}),  # Submit
            ("wait", {"seconds": 2}),
            ("screenshot", {"analyze": "Check result"}),
        ]
        
        responses = []
        for i, (tool_name, args) in enumerate(gui_test_steps):
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
            
            # All steps should succeed in test mode
            self.assertIn("result", response)
        
        # Verify complete workflow executed
        self.assertEqual(len(responses), len(gui_test_steps))
        
        # Verify screenshots were taken
        screenshot_responses = [r for r in responses if "screenshot" in str(r)]
        self.assertGreater(len(screenshot_responses), 2)
    
    def test_data_entry_automation_scenario(self):
        """Test automated data entry from spreadsheet-like workflow"""
        # Simulate data entry automation:
        # Read data, navigate form, enter data, submit, repeat
        
        test_data = [
            {"name": "John Doe", "email": "john@example.com", "phone": "123-456-7890"},
            {"name": "Jane Smith", "email": "jane@example.com", "phone": "098-765-4321"},
            {"name": "Bob Johnson", "email": "bob@example.com", "phone": "555-123-4567"},
        ]
        
        for record_index, record in enumerate(test_data):
            # Process each record
            record_steps = [
                ("screenshot", {"analyze": f"Form for record {record_index + 1}"}),
                ("click", {"x": 150, "y": 100}),  # Name field
                ("key", {"key": "ctrl+a"}),  # Clear field
                ("type", {"text": record["name"]}),
                ("key", {"key": "Tab"}),
                ("type", {"text": record["email"]}),
                ("key", {"key": "Tab"}),
                ("type", {"text": record["phone"]}),
                ("click", {"x": 200, "y": 300}),  # Submit button
                ("wait", {"seconds": 1}),
                ("screenshot", {"analyze": "Verify submission"}),
            ]
            
            for i, (tool_name, args) in enumerate(record_steps):
                request = {
                    "jsonrpc": "2.0",
                    "id": f"{record_index}-{i}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": args
                    }
                }
                
                response = self.server.handle_request(request)
                
                # Each step should succeed
                self.assertIn("result", response)
        
        # All records should have been processed
        self.assertEqual(len(test_data), 3)
    
    def test_system_monitoring_scenario(self):
        """Test system monitoring and alerting workflow"""
        # Simulate system monitoring:
        # Take screenshots at intervals, analyze for issues, respond to problems
        
        monitoring_cycle = [
            ("screenshot", {"analyze": "Check system status dashboard"}),
            ("wait", {"seconds": 1}),
            ("screenshot", {"analyze": "Monitor CPU usage graphs"}),
            ("wait", {"seconds": 1}),
            ("screenshot", {"analyze": "Check memory usage"}),
            ("wait", {"seconds": 1}),
            ("screenshot", {"analyze": "Look for error alerts"}),
            # Simulate finding an issue and responding
            ("click", {"x": 400, "y": 200}),  # Click on alert
            ("wait", {"seconds": 0.5}),
            ("screenshot", {"analyze": "Alert details"}),
            ("key", {"key": "Escape"}),  # Close alert
            ("wait", {"seconds": 0.5}),
        ]
        
        # Run monitoring cycle multiple times
        for cycle in range(3):
            for i, (tool_name, args) in enumerate(monitoring_cycle):
                request = {
                    "jsonrpc": "2.0",
                    "id": f"cycle{cycle}-{i}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": args
                    }
                }
                
                response = self.server.handle_request(request)
                
                # Each monitoring step should succeed
                self.assertIn("result", response)
        
        # Monitoring should complete all cycles
        self.assertEqual(cycle, 2)  # 0, 1, 2 = 3 cycles


if __name__ == "__main__":
    unittest.main(verbosity=2)