"""
End-to-End Tests for MCP

Tests complete workflows from user request to final result,
including error scenarios and automatic recovery.
"""

from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
import tempfile
import unittest

from mcp.core.factory import create_computer_use_for_testing
from mcp.server.mcp_server import ComputerUseServer

#!/usr/bin/env python3

class TestE2EWorkflows(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.server = ComputerUseServer()
        
    def test_screenshot_workflow_no_display_to_success(self):
        """Test complete screenshot workflow from no display to success"""
        # User request: Take screenshot
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {"save_path": "/tmp/e2e_test.png"}
            }
        }
        
        # Simulate WSL2 environment with no initial display
        with patch('mcp.platform_utils.get_platform_info', return_value={
            'platform': 'linux',
            'environment': 'wsl2',
            'display_available': False
        }):
            with patch('subprocess.run') as mock_run:
                # Simulate auto-resolution process
                mock_run.side_effect = [
                    # Get Windows host IP
                    Mock(returncode=0, stdout='nameserver 172.17.0.1'),
                    # First X11 test fails
                    Mock(returncode=1),
                    # VcXsrv installation and start
                    Mock(returncode=0),
                    Mock(returncode=0),
                    Mock(returncode=0),
                    # X11 test succeeds
                    Mock(returncode=0)
                ]
                
                with patch('os.path.exists', return_value=False):  # VcXsrv not installed
                    with patch('time.sleep'):  # Speed up test
                        # Mock screenshot data
                        with patch.object(self.server.computer, 'take_screenshot', 
                                        return_value={'success': True, 'data': b'test_image_data'}):
                            
                            response = self.server.handle_request(request)
                            
                            # Should succeed with auto-resolution
                            self.assertIn('result', response)
                            result = json.loads(response['result']['content'][0]['text'])
                            
                            # Verify success indicators
                            self.assertTrue(
                                result.get('success', False) or 
                                'saved_to' in result or
                                result.get('status') == 'success',
                                f"Screenshot should succeed after auto-resolution: {result}"
                            )
    
    def test_click_workflow_permission_denied_to_success(self):
        """Test click workflow with permission resolution"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 500, "y": 300}
            }
        }
        
        # Mock initial permission error
        with patch.object(self.server.computer, 'click', side_effect=[
            {'success': False, 'error': 'Permission denied'},
            {'success': True, 'action': 'click', 'coordinates': (500, 300)}
        ]):
            with patch('subprocess.run') as mock_run:
                # Mock sudo configuration
                mock_run.return_value = Mock(returncode=0)
                
                with patch.dict(os.environ, {'MCP_USE_SUDO': '0'}):
                    response = self.server.handle_request(request)
                    
                    self.assertIn('result', response)
                    result = json.loads(response['result']['content'][0]['text'])
                    
                    # Should succeed after permission elevation
                    self.assertTrue(
                        result.get('success', False) or
                        result.get('auto_resolved', False),
                        f"Click should succeed after permission resolution: {result}"
                    )
    
    def test_type_workflow_no_focus_to_success(self):
        """Test type workflow with focus preparation"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "Hello, E2E Test!"}
            }
        }
        
        # Mock validation requiring focus
        with patch.object(self.server.validator, 'validate_operation') as mock_validate:
            mock_validate.return_value = Mock(
                status='needs_preparation',
                confidence=0.6,
                issues=['No input field focused'],
                preparations=[{
                    'action': 'focus_window',
                    'params': {'method': 'click_center'}
                }],
                alternatives=[],
                metadata={}
            )
            
            with patch.object(self.server.validator, 'prepare_operation', 
                            return_value=(True, [{'action': 'focus_window', 'success': True}])):
                
                with patch.object(self.server.computer, 'type_text', 
                                return_value={'success': True, 'action': 'type'}):
                    
                    response = self.server.handle_request(request)
                    
                    self.assertIn('result', response)
                    result = json.loads(response['result']['content'][0]['text'])
                    
                    # Should succeed after preparation
                    self.assertTrue(result.get('success', False))
    
    def test_complex_workflow_multiple_errors_to_success(self):
        """Test complex workflow with multiple error types"""
        # Workflow: Screenshot -> Click -> Type
        
        # Step 1: Screenshot with display error
        screenshot_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "screenshot",
                "arguments": {"save_path": "/tmp/workflow_test.png"}
            }
        }
        
        with patch('mcp.auto_resolver.get_auto_resolver') as mock_resolver:
            mock_resolver.return_value.auto_resolve.return_value = (
                True, {'message': 'Display configured'}
            )
            
            with patch.object(self.server.computer, 'take_screenshot',
                            return_value={'success': True, 'data': b'test'}):
                
                response1 = self.server.handle_request(screenshot_request)
                self.assertIn('result', response1)
        
        # Step 2: Click with retry needed
        click_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 100, "y": 100}
            }
        }
        
        attempt_count = 0
        def mock_click(x, y, button='left'):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                return {'success': False, 'error': 'Temporary failure'}
            return {'success': True, 'action': 'click'}
        
        with patch.object(self.server.computer, 'click', side_effect=mock_click):
            response2 = self.server.handle_request(click_request)
            self.assertIn('result', response2)
        
        # Step 3: Type with safety check
        type_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "type",
                "arguments": {"text": "Workflow complete!"}
            }
        }
        
        with patch.object(self.server.computer, 'type_text',
                        return_value={'success': True, 'action': 'type'}):
            response3 = self.server.handle_request(type_request)
            self.assertIn('result', response3)
        
        # All steps should complete successfully
        for response in [response1, response2, response3]:
            result = json.loads(response['result']['content'][0]['text'])
            self.assertTrue(
                result.get('success', False) or 
                result.get('status') == 'success' or
                'error' not in result,
                f"Step should succeed: {result}"
            )

class TestE2EPlatformScenarios(unittest.TestCase):
    """Test platform-specific E2E scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.server = ComputerUseServer()
    
    def test_wsl2_complete_setup_workflow(self):
        """Test complete WSL2 setup from scratch"""
        # Simulate fresh WSL2 environment
        with patch('mcp.auto_resolver.AutoResolver._detect_wsl', return_value=True):
            with patch.dict(os.environ, {'DISPLAY': ''}):
                
                # User tries to take screenshot
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "screenshot",
                        "arguments": {"save_path": "~/first_screenshot.png"}
                    }
                }
                
                with patch('subprocess.run') as mock_run:
                    # Simulate complete auto-setup
                    mock_run.side_effect = [
                        # Get host IP
                        Mock(returncode=0, stdout='nameserver 172.17.0.1'),
                        # X11 test fails
                        Mock(returncode=1),
                        # Download VcXsrv
                        Mock(returncode=0),
                        # Install VcXsrv
                        Mock(returncode=0),
                        # Configure firewall
                        Mock(returncode=0),
                        # Start VcXsrv
                        Mock(returncode=0),
                        # X11 test succeeds
                        Mock(returncode=0)
                    ]
                    
                    with patch('os.path.exists', return_value=False):
                        with patch('time.sleep'):
                            with patch.object(self.server.computer, 'take_screenshot',
                                            return_value={'success': True, 'data': b'img'}):
                                
                                response = self.server.handle_request(request)
                                
                                # Should complete successfully
                                self.assertIn('result', response)
                                
                                # DISPLAY should be set
                                self.assertNotEqual(os.environ.get('DISPLAY', ''), '')
    
    def test_docker_container_workflow(self):
        """Test Docker container automation setup"""
        with patch('os.path.exists', return_value=True):  # /.dockerenv
            # User tries to click in Docker container
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "click",
                    "arguments": {"x": 200, "y": 200}
                }
            }
            
            with patch('subprocess.run') as mock_run:
                # Simulate Docker display setup
                mock_run.side_effect = [
                    # xhost command
                    Mock(returncode=0),
                    # X11 test
                    Mock(returncode=0)
                ]
                
                with patch.object(self.server.computer, 'click',
                                return_value={'success': True, 'action': 'click'}):
                    
                    response = self.server.handle_request(request)
                    
                    self.assertIn('result', response)
                    result = json.loads(response['result']['content'][0]['text'])
                    self.assertTrue(result.get('success', False))
    
    def test_headless_server_workflow(self):
        """Test headless server with virtual display"""
        with patch('mcp.platform_utils.get_platform_info', return_value={
            'platform': 'linux',
            'environment': 'server',
            'display_available': False,
            'has_gui': False
        }):
            # User tries to take screenshot on headless server
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"save_path": "/tmp/headless.png"}
                }
            }
            
            with patch('subprocess.run') as mock_run:
                # Simulate Xvfb setup
                mock_run.side_effect = [
                    # Start Xvfb
                    Mock(returncode=0),
                    # Test display
                    Mock(returncode=0)
                ]
                
                with patch('shutil.which', return_value='/usr/bin/Xvfb'):
                    with patch.object(self.server.computer, 'take_screenshot',
                                    return_value={'success': True, 'data': b'virtual'}):
                        
                        response = self.server.handle_request(request)
                        
                        self.assertIn('result', response)
                        result = json.loads(response['result']['content'][0]['text'])
                        
                        # Should work with virtual display
                        self.assertTrue(
                            result.get('success', False) or
                            result.get('auto_fallback', False),
                            f"Should work with virtual display: {result}"
                        )

class TestE2ESafetyScenarios(unittest.TestCase):
    """Test E2E safety scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.server = ComputerUseServer()
    
    def test_dangerous_command_blocked(self):
        """Test dangerous commands are blocked at all levels"""
        dangerous_commands = [
            "rm -rf /",
            "format c:",
            ":(){ :|:& };:",  # Fork bomb
            "dd if=/dev/zero of=/dev/sda"
        ]
        
        for cmd in dangerous_commands:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "type",
                    "arguments": {"text": cmd}
                }
            }
            
            response = self.server.handle_request(request)
            self.assertIn('result', response)
            
            result = json.loads(response['result']['content'][0]['text'])
            
            # Should be blocked
            self.assertTrue(
                'blocked' in str(result).lower() or
                'safety' in str(result).lower() or
                result.get('success') is False,
                f"Dangerous command should be blocked: {cmd}"
            )
    
    def test_safe_mode_prevents_modifications(self):
        """Test safe mode prevents system modifications"""
        with patch.dict(os.environ, {'MCP_SAFE_MODE': '1'}):
            # Try to install software
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "screenshot",
                    "arguments": {"save_path": "/tmp/safe_mode_test.png"}
                }
            }
            
            with patch('subprocess.run') as mock_run:
                response = self.server.handle_request(request)
                
                # Should not attempt installations in safe mode
                install_calls = [
                    call for call in mock_run.call_args_list
                    if 'install' in str(call).lower()
                ]
                
                self.assertEqual(
                    len(install_calls), 0,
                    "Safe mode should prevent installations"
                )
    
    def test_dry_run_mode(self):
        """Test dry run mode logs but doesn't execute"""
        with patch.dict(os.environ, {'MCP_DRY_RUN': '1'}):
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "click",
                    "arguments": {"x": 100, "y": 100}
                }
            }
            
            with patch('subprocess.run') as mock_run:
                with patch('logging.info') as mock_log:
                    response = self.server.handle_request(request)
                    
                    # Should not execute system commands
                    self.assertEqual(
                        mock_run.call_count, 0,
                        "Dry run should not execute commands"
                    )

def run_e2e_tests():
    """Run all E2E tests"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_e2e_tests()