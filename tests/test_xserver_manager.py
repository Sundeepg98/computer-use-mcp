#!/usr/bin/env python3
"""
Test suite for XServerManager functionality
Tests all X server management capabilities including WSL2 support
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call, mock_open
import subprocess
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from computer_use_mcp.xserver_manager import XServerManager


class TestXServerManagerInit(unittest.TestCase):
    """Test XServerManager initialization"""
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 WSL2')
    def test_detect_wsl_true(self, mock_file):
        """Test WSL detection returns True when in WSL"""
        manager = XServerManager()
        self.assertTrue(manager.wsl_mode)
        mock_file.assert_called_with('/proc/version', 'r')
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 generic')
    def test_detect_wsl_false(self, mock_file):
        """Test WSL detection returns False when not in WSL"""
        manager = XServerManager()
        self.assertFalse(manager.wsl_mode)
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_detect_wsl_file_not_found(self, mock_file):
        """Test WSL detection handles missing /proc/version"""
        manager = XServerManager()
        self.assertFalse(manager.wsl_mode)
    
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 WSL2')
    def test_get_host_ip_in_wsl(self, mock_file, mock_run):
        """Test getting Windows host IP in WSL"""
        mock_run.return_value = Mock(
            stdout='nameserver 192.168.1.1\nsearch local',
            returncode=0
        )
        manager = XServerManager()
        self.assertEqual(manager.host_ip, '192.168.1.1')
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 generic')
    def test_get_host_ip_not_wsl(self, mock_file):
        """Test host IP is None when not in WSL"""
        manager = XServerManager()
        self.assertIsNone(manager.host_ip)


class TestXServerAvailability(unittest.TestCase):
    """Test X server availability checking"""
    
    def setUp(self):
        self.manager = XServerManager()
    
    @patch('subprocess.run')
    @patch.dict(os.environ, {'DISPLAY': ':0'})
    def test_check_xserver_available_success(self, mock_run):
        """Test successful X server connection"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=b'Keyboard Control:\n  auto repeat:  on'
        )
        
        result = self.manager.check_xserver_available()
        
        self.assertTrue(result['available'])
        self.assertEqual(result['display'], ':0')
        self.assertEqual(result['method'], 'native_x11')
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_check_xserver_available_failure(self, mock_run):
        """Test failed X server connection"""
        mock_run.side_effect = subprocess.TimeoutExpired('xset', 5)
        
        result = self.manager.check_xserver_available(':0')
        
        self.assertFalse(result['available'])
        self.assertEqual(result['display'], ':0')
        self.assertIn('error', result)
    
    @patch('subprocess.run')
    def test_check_xserver_custom_display(self, mock_run):
        """Test checking custom display"""
        mock_run.return_value = Mock(returncode=1)
        
        result = self.manager.check_xserver_available(':99')
        
        self.assertEqual(result['display'], ':99')
        mock_run.assert_called_once()
        # Check DISPLAY was set in the subprocess environment
        call_env = mock_run.call_args[1]['env']
        self.assertEqual(call_env['DISPLAY'], ':99')


class TestXServerPackageInstallation(unittest.TestCase):
    """Test X server package installation"""
    
    def setUp(self):
        self.manager = XServerManager()
    
    @patch('subprocess.run')
    def test_install_packages_all_success(self, mock_run):
        """Test successful installation of all packages"""
        # Mock dpkg checks (all not installed)
        mock_run.side_effect = [
            Mock(returncode=1),  # xorg not installed
            Mock(returncode=0),  # xorg install success
            Mock(returncode=1),  # xserver-xorg not installed
            Mock(returncode=0),  # xserver-xorg install success
            Mock(returncode=1),  # xvfb not installed
            Mock(returncode=0),  # xvfb install success
            Mock(returncode=1),  # x11-apps not installed
            Mock(returncode=0),  # x11-apps install success
            Mock(returncode=1),  # x11-utils not installed
            Mock(returncode=0),  # x11-utils install success
            Mock(returncode=1),  # xdotool not installed
            Mock(returncode=0),  # xdotool install success
            Mock(returncode=1),  # scrot not installed
            Mock(returncode=0),  # scrot install success
            Mock(returncode=1),  # imagemagick not installed
            Mock(returncode=0),  # imagemagick install success
        ]
        
        result = self.manager.install_xserver_packages()
        
        self.assertEqual(len(result['installed']), 8)
        self.assertEqual(len(result['failed']), 0)
        self.assertEqual(len(result['already_installed']), 0)
    
    @patch('subprocess.run')
    def test_install_packages_some_already_installed(self, mock_run):
        """Test installation when some packages already exist"""
        mock_run.side_effect = [
            Mock(returncode=0),  # xorg already installed
            Mock(returncode=1),  # xserver-xorg not installed
            Mock(returncode=0),  # xserver-xorg install success
            Mock(returncode=0),  # xvfb already installed
            Mock(returncode=1),  # x11-apps not installed
            Mock(returncode=0),  # x11-apps install success
            Mock(returncode=0),  # x11-utils already installed
            Mock(returncode=0),  # xdotool already installed
            Mock(returncode=0),  # scrot already installed
            Mock(returncode=0),  # imagemagick already installed
        ]
        
        result = self.manager.install_xserver_packages()
        
        self.assertEqual(len(result['installed']), 2)
        self.assertEqual(len(result['already_installed']), 6)
        self.assertEqual(len(result['failed']), 0)
    
    @patch('subprocess.run')
    def test_install_packages_with_failures(self, mock_run):
        """Test installation with some failures"""
        mock_run.side_effect = [
            Mock(returncode=1),  # xorg not installed
            Mock(returncode=1, stderr=b'Permission denied'),  # xorg install fail
            Mock(returncode=1),  # xserver-xorg not installed
            Mock(returncode=0),  # xserver-xorg install success
            Mock(returncode=1),  # xvfb not installed
            subprocess.TimeoutExpired('apt-get', 300),  # xvfb install timeout
            Mock(returncode=0),  # x11-apps already installed
            Mock(returncode=0),  # x11-utils already installed
            Mock(returncode=0),  # xdotool already installed
            Mock(returncode=0),  # scrot already installed
            Mock(returncode=0),  # imagemagick already installed
        ]
        
        result = self.manager.install_xserver_packages()
        
        self.assertEqual(len(result['installed']), 1)
        self.assertEqual(len(result['failed']), 2)
        self.assertEqual(len(result['already_installed']), 5)
        
        # Check failure details
        failed_packages = [f['package'] for f in result['failed']]
        self.assertIn('xorg', failed_packages)
        self.assertIn('xvfb', failed_packages)


class TestVirtualDisplay(unittest.TestCase):
    """Test virtual display (Xvfb) functionality"""
    
    def setUp(self):
        self.manager = XServerManager()
    
    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_virtual_display_success(self, mock_sleep, mock_popen):
        """Test successful virtual display start"""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        with patch.object(self.manager, 'check_xserver_available') as mock_check:
            mock_check.return_value = {'available': True}
            
            result = self.manager.start_virtual_display(99, 1920, 1080)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['display'], ':99')
            self.assertEqual(result['pid'], 12345)
            self.assertEqual(result['resolution'], '1920x1080')
            
            # Verify Xvfb command
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            self.assertEqual(cmd[0], 'Xvfb')
            self.assertEqual(cmd[1], ':99')
            self.assertIn('1920x1080x24', cmd)
    
    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_virtual_display_already_running(self, mock_sleep, mock_popen):
        """Test starting display that's already running"""
        # Add display to manager's tracking
        self.manager.xserver_processes[':99'] = Mock(pid=11111)
        
        result = self.manager.start_virtual_display(99)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'already_running')
        self.assertEqual(result['pid'], 11111)
        mock_popen.assert_not_called()
    
    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_virtual_display_failure(self, mock_sleep, mock_popen):
        """Test virtual display start failure"""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        with patch.object(self.manager, 'check_xserver_available') as mock_check:
            mock_check.return_value = {'available': False}
            
            result = self.manager.start_virtual_display(99)
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            mock_process.terminate.assert_called_once()
    
    def test_stop_xserver_success(self):
        """Test successful X server stop"""
        mock_process = Mock()
        mock_process.wait.return_value = None
        
        self.manager.xserver_processes[':99'] = mock_process
        self.manager.display_ports[':99'] = {'width': 1920, 'height': 1080, 'pid': 12345}
        
        result = self.manager.stop_xserver(':99')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['display'], ':99')
        self.assertEqual(result['status'], 'stopped')
        mock_process.terminate.assert_called_once()
        self.assertNotIn(':99', self.manager.xserver_processes)
        self.assertNotIn(':99', self.manager.display_ports)
    
    def test_stop_xserver_not_found(self):
        """Test stopping non-existent X server"""
        result = self.manager.stop_xserver(':99')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_cleanup_all(self):
        """Test cleaning up all X servers"""
        # Add multiple displays
        for i in range(3):
            mock_process = Mock()
            self.manager.xserver_processes[f':{99+i}'] = mock_process
            self.manager.display_ports[f':{99+i}'] = {'pid': 12345+i}
        
        result = self.manager.cleanup_all()
        
        self.assertEqual(result['stopped_servers'], 3)
        self.assertEqual(len(self.manager.xserver_processes), 0)
        self.assertEqual(len(self.manager.display_ports), 0)


class TestWSLXForwarding(unittest.TestCase):
    """Test WSL2 X11 forwarding functionality"""
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 WSL2')
    @patch('subprocess.run')
    def test_setup_wsl_xforwarding_success(self, mock_run, mock_file):
        """Test successful WSL X forwarding setup"""
        mock_run.return_value = Mock(
            stdout='nameserver 192.168.1.100\n',
            returncode=0
        )
        
        manager = XServerManager()
        
        with patch.object(manager, 'check_xserver_available') as mock_check:
            mock_check.return_value = {'available': True}
            
            result = manager.setup_wsl_xforwarding()
            
            self.assertTrue(result['success'])
            self.assertEqual(result['display'], '192.168.1.100:0.0')
            self.assertEqual(result['host_ip'], '192.168.1.100')
            self.assertEqual(os.environ.get('DISPLAY'), '192.168.1.100:0.0')
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 generic')
    def test_setup_wsl_xforwarding_not_wsl(self, mock_file):
        """Test X forwarding setup when not in WSL"""
        manager = XServerManager()
        
        result = manager.setup_wsl_xforwarding()
        
        self.assertFalse(result['success'])
        self.assertIn('Not running in WSL', result['error'])
    
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 WSL2')
    @patch('subprocess.run')
    def test_setup_wsl_xforwarding_no_xserver(self, mock_run, mock_file):
        """Test X forwarding when Windows X server not available"""
        mock_run.return_value = Mock(
            stdout='nameserver 192.168.1.100\n',
            returncode=0
        )
        
        manager = XServerManager()
        
        with patch.object(manager, 'check_xserver_available') as mock_check:
            mock_check.return_value = {'available': False}
            
            result = manager.setup_wsl_xforwarding()
            
            self.assertFalse(result['success'])
            self.assertIn('Windows X server not accessible', result['error'])
            self.assertIn('suggestion', result)


class TestGetBestDisplay(unittest.TestCase):
    """Test automatic display selection logic"""
    
    def setUp(self):
        self.manager = XServerManager()
    
    @patch.dict(os.environ, {'DISPLAY': ':0'})
    def test_get_best_display_existing_valid(self):
        """Test using existing valid DISPLAY"""
        with patch.object(self.manager, 'check_xserver_available') as mock_check:
            mock_check.return_value = {'available': True, 'display': ':0'}
            
            result = self.manager.get_best_display()
            
            self.assertTrue(result['available'])
            self.assertEqual(result['display'], ':0')
            self.assertEqual(result['method'], 'existing_display')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='Linux version 5.10 WSL2')
    def test_get_best_display_wsl_forwarding(self, mock_file, mock_run):
        """Test WSL forwarding as second choice"""
        # Mock subprocess for host IP detection
        mock_run.return_value = Mock(
            stdout='nameserver 192.168.1.100\n',
            returncode=0
        )
        
        # Create new manager with WSL mode
        with patch('computer_use_mcp.xserver_manager.XServerManager._detect_wsl', return_value=True):
            manager = XServerManager()
            manager.wsl_mode = True
            manager.host_ip = '192.168.1.100'
            
            with patch.object(manager, 'setup_wsl_xforwarding') as mock_wsl:
                mock_wsl.return_value = {
                    'success': True,
                    'display': '192.168.1.100:0.0',
                    'host_ip': '192.168.1.100'
                }
                
                result = manager.get_best_display()
                
                self.assertTrue(result['available'])
                self.assertEqual(result['method'], 'wsl_xforwarding')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_best_display_virtual(self):
        """Test virtual display as third choice"""
        self.manager.wsl_mode = False  # Not in WSL
        
        with patch.object(self.manager, 'start_virtual_display') as mock_virtual:
            mock_virtual.return_value = {
                'success': True,
                'display': ':99',
                'pid': 12345
            }
            
            result = self.manager.get_best_display()
            
            self.assertTrue(result['available'])
            self.assertEqual(result['display'], ':99')
            self.assertEqual(result['method'], 'virtual_display')
            self.assertEqual(os.environ.get('DISPLAY'), ':99')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_best_display_native_fallback(self):
        """Test native X server as last resort"""
        self.manager.wsl_mode = False
        
        with patch.object(self.manager, 'start_virtual_display') as mock_virtual:
            mock_virtual.return_value = {'success': False}
            
            with patch.object(self.manager, 'check_xserver_available') as mock_check:
                mock_check.return_value = {
                    'available': True,
                    'display': ':0',
                    'method': 'native_x11'
                }
                
                result = self.manager.get_best_display()
                
                self.assertTrue(result['available'])
                self.assertEqual(result['display'], ':0')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_best_display_none_available(self):
        """Test when no display is available"""
        self.manager.wsl_mode = False
        
        with patch.object(self.manager, 'start_virtual_display') as mock_virtual:
            mock_virtual.return_value = {'success': False}
            
            with patch.object(self.manager, 'check_xserver_available') as mock_check:
                mock_check.return_value = {'available': False}
                
                result = self.manager.get_best_display()
                
                self.assertFalse(result['available'])
                self.assertIn('error', result)
                self.assertIn('suggestions', result)
                self.assertEqual(len(result['suggestions']), 4)


class TestXServerStatus(unittest.TestCase):
    """Test X server status reporting"""
    
    def setUp(self):
        self.manager = XServerManager()
    
    @patch.dict(os.environ, {'DISPLAY': ':0'})
    def test_get_status(self):
        """Test getting X server status"""
        # Setup some managed servers
        self.manager.xserver_processes[':99'] = Mock(pid=12345)
        self.manager.display_ports[':99'] = {
            'width': 1920,
            'height': 1080,
            'pid': 12345
        }
        
        status = self.manager.get_status()
        
        self.assertEqual(status['current_display'], ':0')
        self.assertEqual(status['active_processes'], 1)
        self.assertIn(':99', status['managed_servers'])
        self.assertEqual(status['managed_servers'][':99']['pid'], 12345)
        self.assertEqual(status['managed_servers'][':99']['resolution'], '1920x1080')


if __name__ == '__main__':
    unittest.main()