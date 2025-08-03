#!/usr/bin/env python3
"""
End-to-End tests for computer-use-mcp
Tests complete workflows from user perspective
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import sys
import os
import subprocess
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mcp_server import ComputerUseServer
from computer_use_core import ComputerUseCore
from safety_checks import SafetyChecker
from visual_analyzer import VisualAnalyzerAdvanced


class TestE2EWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        """Setup E2E test environment"""
        self.server = ComputerUseServer(test_mode=True)
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_e2e_form_filling_workflow(self):
        """Test complete form filling workflow"""
        # Workflow: Screenshot -> Find form -> Fill fields -> Submit
        
        workflow_steps = []
        
        # Step 1: Take screenshot to find form
        screenshot_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {
                    "analyze": "Find login form with username and password fields"
                }
            }
        }
        
        with patch.object(self.server.computer, 'screenshot') as mock_screenshot:
            mock_screenshot.return_value = {
                'status': 'success',
                'data': 'mock_screenshot_data',
                'analysis': {
                    'form_found': True,
                    'username_field': {'x': 400, 'y': 300},
                    'password_field': {'x': 400, 'y': 350},
                    'submit_button': {'x': 450, 'y': 400}
                }
            }
            
            response = self.server.handle_tool_call(screenshot_request)
            workflow_steps.append(('screenshot', response))
            self.assertIn('result', response)
        
        # Step 2: Click on username field
        click_username_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 400, "y": 300}
            }
        }
        
        with patch.object(self.server.computer, 'click') as mock_click:
            mock_click.return_value = {'success': True}
            response = self.server.handle_tool_call(click_username_request)
            workflow_steps.append(('click_username', response))
            self.assertIn('result', response)
        
        # Step 3: Type username
        type_username_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "test_user@example.com"}
            }
        }
        
        with patch.object(self.server.computer, 'type_text') as mock_type:
            mock_type.return_value = {'success': True}
            response = self.server.handle_tool_call(type_username_request)
            workflow_steps.append(('type_username', response))
            self.assertIn('result', response)
        
        # Step 4: Tab to password field
        tab_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "key",
                "arguments": {"key": "Tab"}
            }
        }
        
        with patch.object(self.server.computer, 'key_press') as mock_key:
            mock_key.return_value = {'success': True}
            response = self.server.handle_tool_call(tab_request)
            workflow_steps.append(('tab_to_password', response))
            self.assertIn('result', response)
        
        # Step 5: Type password
        type_password_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "SecurePassword123!"}
            }
        }
        
        with patch.object(self.server.computer, 'type_text') as mock_type:
            mock_type.return_value = {'success': True}
            response = self.server.handle_tool_call(type_password_request)
            workflow_steps.append(('type_password', response))
            self.assertIn('result', response)
        
        # Step 6: Click submit button
        click_submit_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 450, "y": 400}
            }
        }
        
        with patch.object(self.server.computer, 'click') as mock_click:
            mock_click.return_value = {'success': True}
            response = self.server.handle_tool_call(click_submit_request)
            workflow_steps.append(('click_submit', response))
            self.assertIn('result', response)
        
        # Verify workflow completed successfully
        self.assertEqual(len(workflow_steps), 6)
        for step_name, response in workflow_steps:
            self.assertIn('result', response, f"Step {step_name} failed")
    
    def test_e2e_navigation_workflow(self):
        """Test website navigation workflow"""
        # Workflow: Open page -> Find nav -> Click links -> Verify
        
        # Step 1: Take screenshot
        response1 = self._execute_tool_call("screenshot", {
            "analyze": "Find navigation menu"
        })
        self.assertIn('result', response1)
        
        # Step 2: Click on menu item
        response2 = self._execute_tool_call("click", {
            "x": 200, "y": 50
        })
        self.assertIn('result', response2)
        
        # Step 3: Wait for page load
        response3 = self._execute_tool_call("wait", {
            "seconds": 1
        })
        self.assertIn('result', response3)
        
        # Step 4: Scroll down to see content
        response4 = self._execute_tool_call("scroll", {
            "direction": "down",
            "amount": 5
        })
        self.assertIn('result', response4)
        
        # Step 5: Take another screenshot to verify
        response5 = self._execute_tool_call("screenshot", {
            "analyze": "Verify we are on the new page"
        })
        self.assertIn('result', response5)
    
    def test_e2e_drag_and_drop_workflow(self):
        """Test drag and drop workflow"""
        # Workflow: Find draggable -> Find drop zone -> Drag -> Verify
        
        # Step 1: Screenshot to find elements
        with patch.object(self.server.visual, 'analyze_visual_context') as mock_analyze:
            mock_analyze.return_value = {
                'draggable': {'x': 100, 'y': 200},
                'drop_zone': {'x': 500, 'y': 200}
            }
            
            response1 = self._execute_tool_call("screenshot", {
                "analyze": "Find draggable element and drop zone"
            })
            self.assertIn('result', response1)
        
        # Step 2: Perform drag operation
        response2 = self.server.handle_tool_call({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "drag",
                "arguments": {
                    "start_x": 100,
                    "start_y": 200,
                    "end_x": 500,
                    "end_y": 200
                }
            }
        })
        self.assertIn('result', response2)
        
        # Step 3: Verify with screenshot
        response3 = self._execute_tool_call("screenshot", {
            "analyze": "Verify element was dropped successfully"
        })
        self.assertIn('result', response3)
    
    def test_e2e_automation_workflow(self):
        """Test the automate tool for complex tasks"""
        # Use automate tool to handle complex workflow
        
        automate_request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "automate",
                "arguments": {
                    "task": "Fill out contact form with name John Doe and email john@example.com"
                }
            }
        }
        
        with patch.object(self.server.visual, 'plan_actions') as mock_plan:
            # Mock the visual analyzer's plan
            mock_plan.return_value = [
                {
                    'action': 'screenshot',
                    'purpose': 'Find contact form'
                },
                {
                    'action': 'click',
                    'coordinates': {'x': 400, 'y': 200},
                    'target': 'name field'
                },
                {
                    'action': 'type',
                    'text': 'John Doe'
                },
                {
                    'action': 'click',
                    'coordinates': {'x': 400, 'y': 250},
                    'target': 'email field'
                },
                {
                    'action': 'type',
                    'text': 'john@example.com'
                },
                {
                    'action': 'click',
                    'coordinates': {'x': 450, 'y': 350},
                    'target': 'submit button'
                }
            ]
            
            response = self.server.handle_tool_call(automate_request)
            
            # Verify planning was called
            mock_plan.assert_called_once()
            
            # Verify response contains the plan
            self.assertIn('result', response)
            # Result is MCP-formatted with content array
            self.assertIn('content', response['result'])
            content = response['result']['content'][0]
            self.assertEqual(content['type'], 'text')
            # Parse the JSON text content
            result_data = json.loads(content['text'])
            self.assertIn('plan', result_data)
            self.assertIn('task', result_data)
            self.assertEqual(result_data['task'], "Fill out contact form with name John Doe and email john@example.com")
    
    def test_e2e_error_recovery_workflow(self):
        """Test workflow with error recovery"""
        # Simulate a workflow where something fails and needs recovery
        
        # Step 1: Try to click, but it fails
        with patch.object(self.server.computer, 'click') as mock_click:
            mock_click.side_effect = Exception("Element not found")
            
            response1 = self.server.handle_tool_call({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "click",
                    "arguments": {"x": 100, "y": 100}
                }
            })
            
            # Should get error response
            self.assertIn('error', response1)
        
        # Step 2: Take screenshot to diagnose
        response2 = self._execute_tool_call("screenshot", {
            "analyze": "Find clickable elements on screen"
        })
        self.assertIn('result', response2)
        
        # Step 3: Try alternative approach - use key navigation
        response3 = self._execute_tool_call("key", {
            "key": "Tab"
        })
        self.assertIn('result', response3)
        
        # Step 4: Try pressing Enter instead of clicking
        response4 = self._execute_tool_call("key", {
            "key": "Return"
        })
        self.assertIn('result', response4)
        
        # Workflow adapted and completed despite initial error
    
    def test_e2e_multi_window_workflow(self):
        """Test workflow across multiple windows"""
        # Workflow: Open new window -> Switch -> Interact -> Switch back
        
        # Step 1: Press Ctrl+N to open new window
        response1 = self._execute_tool_call("key", {
            "key": "ctrl+n"
        })
        self.assertIn('result', response1)
        
        # Step 2: Wait for new window
        response2 = self._execute_tool_call("wait", {
            "seconds": 0.5
        })
        self.assertIn('result', response2)
        
        # Step 3: Type URL in new window
        response3 = self._execute_tool_call("type", {
            "text": "https://example.com"
        })
        self.assertIn('result', response3)
        
        # Step 4: Press Enter to navigate
        response4 = self._execute_tool_call("key", {
            "key": "Return"
        })
        self.assertIn('result', response4)
        
        # Step 5: Switch back with Alt+Tab
        response5 = self._execute_tool_call("key", {
            "key": "alt+Tab"
        })
        self.assertIn('result', response5)
    
    def test_e2e_copy_paste_workflow(self):
        """Test copy and paste workflow"""
        # Workflow: Select text -> Copy -> Navigate -> Paste
        
        # Step 1: Triple-click to select line
        response1 = self._execute_tool_call("click", {
            "x": 300, "y": 200,
            "button": "left"
        })
        self.assertIn('result', response1)
        
        # Click twice more for triple-click
        response2 = self._execute_tool_call("click", {
            "x": 300, "y": 200,
            "button": "left"  
        })
        self.assertIn('result', response2)
        
        response3 = self._execute_tool_call("click", {
            "x": 300, "y": 200,
            "button": "left"
        })
        self.assertIn('result', response3)
        
        # Step 2: Copy selection
        response4 = self._execute_tool_call("key", {
            "key": "ctrl+c"
        })
        self.assertIn('result', response4)
        
        # Step 3: Click in another field
        response5 = self._execute_tool_call("click", {
            "x": 400, "y": 300
        })
        self.assertIn('result', response5)
        
        # Step 4: Paste
        response6 = self._execute_tool_call("key", {
            "key": "ctrl+v"
        })
        self.assertIn('result', response6)
    
    def test_e2e_performance_workflow(self):
        """Test workflow performance and timing"""
        import time
        
        start_time = time.time()
        workflow_times = []
        
        # Execute a series of operations and measure time
        operations = [
            ("screenshot", {"analyze": "test"}),
            ("click", {"x": 100, "y": 100}),
            ("type", {"text": "performance test"}),
            ("key", {"key": "Enter"}),
            ("wait", {"seconds": 0.1}),
            ("scroll", {"direction": "down", "amount": 3})
        ]
        
        for op_name, args in operations:
            op_start = time.time()
            response = self._execute_tool_call(op_name, args)
            op_time = time.time() - op_start
            workflow_times.append((op_name, op_time))
            self.assertIn('result', response)
        
        total_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(total_time, 5.0, "Workflow took too long")
        
        # Check individual operation times
        for op_name, op_time in workflow_times:
            if op_name != "wait":
                self.assertLess(op_time, 1.0, f"{op_name} took too long: {op_time}s")
    
    def _execute_tool_call(self, tool_name, arguments):
        """Helper to execute tool calls"""
        request = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Map tool names to actual method names
        method_map = {
            'screenshot': 'screenshot',
            'click': 'click',
            'type': 'type_text',
            'key': 'key_press',
            'scroll': 'scroll',
            'drag': 'drag',
            'wait': 'wait'
        }
        
        method_name = method_map.get(tool_name, tool_name.replace('-', '_'))
        
        # Mock the underlying computer operations in test mode
        with patch.object(self.server.computer, method_name, 
                         return_value={'success': True, 'test_mode': True}):
            return self.server.handle_tool_call(request)


class TestE2EEdgeCases(unittest.TestCase):
    """Test E2E edge cases and error scenarios"""
    
    def setUp(self):
        """Setup test environment"""
        self.server = ComputerUseServer(test_mode=True)
    
    def test_e2e_no_display_fallback(self):
        """Test E2E workflow when display is not available"""
        # Simulate no display environment
        with patch.object(self.server.computer, 'display_available', False):
            # Try to execute visual operations
            response1 = self.server.handle_tool_call({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"analyze": "test"}
                }
            })
            
            # Should still return a response (possibly with limitations)
            self.assertIn('result', response1)
    
    def test_e2e_rapid_operations(self):
        """Test rapid successive operations"""
        # Execute many operations quickly
        responses = []
        
        for i in range(10):
            response = self.server.handle_tool_call({
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "key",
                    "arguments": {"key": chr(65 + i)}  # A, B, C, etc.
                }
            })
            responses.append(response)
        
        # All should succeed
        self.assertEqual(len(responses), 10)
        for response in responses:
            self.assertIn('result', response)
    
    def test_e2e_safety_in_workflow(self):
        """Test safety checks don't break workflows"""
        # Workflow with some potentially dangerous operations
        
        # Safe operation
        response1 = self.server.handle_tool_call({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "Hello World"}
            }
        })
        self.assertIn('result', response1)
        
        # Dangerous operation - should be blocked
        response2 = self.server.handle_tool_call({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "rm -rf /"}
            }
        })
        self.assertIn('error', response2)
        
        # Workflow should continue after blocked operation
        response3 = self.server.handle_tool_call({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "Safe text again"}
            }
        })
        self.assertIn('result', response3)


if __name__ == '__main__':
    unittest.main(verbosity=2)