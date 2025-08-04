#!/usr/bin/env python3
"""
Windows Server Core screenshot handler
Provides alternative solutions for GUI-less server environments
"""

import logging
from typing import Optional, Dict, Any
from .base import ScreenshotBase, ScreenshotCaptureError

logger = logging.getLogger(__name__)


class ServerCoreScreenshot(ScreenshotBase):
    """Handler for Windows Server Core (no GUI) environments"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Server Core handler"""
        super().__init__(config)
        self.alternatives = self._get_alternatives()
        
    def capture(self, **kwargs) -> bytes:
        """Capture not available on Server Core - raise with helpful message"""
        analyze = kwargs.get('analyze', '')
        
        error_msg = (
            "Screenshot capture is not available on Windows Server Core (no GUI). "
            f"Request: '{analyze}'\n\n"
            "Available alternatives:\n"
        )
        
        for alt in self.alternatives:
            error_msg += f"  • {alt['name']}: {alt['description']}\n"
            
        error_msg += "\nFor GUI operations, consider:\n"
        error_msg += "  • Installing Server with Desktop Experience\n"
        error_msg += "  • Using Windows Admin Center for web-based management\n"
        error_msg += "  • Connecting via RDP to a server with GUI\n"
        
        raise ScreenshotCaptureError(error_msg)
    
    def _get_alternatives(self) -> list:
        """Get alternative automation methods for Server Core"""
        return [
            {
                'name': 'PowerShell Remoting',
                'description': 'Use Enter-PSSession or Invoke-Command for remote automation',
                'example': 'Enter-PSSession -ComputerName server-core-01'
            },
            {
                'name': 'Windows Admin Center',
                'description': 'Web-based GUI for server management',
                'example': 'https://server-core-01:6516'
            },
            {
                'name': 'Server Manager Remote',
                'description': 'Manage Server Core from a GUI server',
                'example': 'Add server in Server Manager on GUI system'
            },
            {
                'name': 'PowerShell Direct',
                'description': 'For Hyper-V VMs, use PowerShell Direct',
                'example': 'Enter-PSSession -VMName ServerCoreVM'
            },
            {
                'name': 'RSAT Tools',
                'description': 'Remote Server Administration Tools from Windows 10/11',
                'example': 'Install RSAT and use MMC snap-ins'
            }
        ]
    
    def suggest_automation(self, task: str) -> Dict[str, Any]:
        """Suggest automation approach for given task on Server Core"""
        suggestions = {
            'task': task,
            'approaches': []
        }
        
        # Analyze task and suggest appropriate tools
        task_lower = task.lower()
        
        if 'service' in task_lower or 'process' in task_lower:
            suggestions['approaches'].append({
                'method': 'PowerShell',
                'commands': [
                    'Get-Service | Where-Object {$_.Status -eq "Running"}',
                    'Get-Process | Sort-Object CPU -Descending | Select-Object -First 10',
                    'Restart-Service -Name "ServiceName"'
                ]
            })
            
        elif 'file' in task_lower or 'folder' in task_lower:
            suggestions['approaches'].append({
                'method': 'PowerShell',
                'commands': [
                    'Get-ChildItem -Path C:\\ -Recurse -Filter "*.log"',
                    'New-Item -ItemType Directory -Path "C:\\NewFolder"',
                    'Copy-Item -Path "source" -Destination "dest" -Recurse'
                ]
            })
            
        elif 'network' in task_lower or 'ip' in task_lower:
            suggestions['approaches'].append({
                'method': 'PowerShell/NetSh',
                'commands': [
                    'Get-NetAdapter | Select-Object Name, Status, LinkSpeed',
                    'Get-NetIPAddress | Format-Table IPAddress, InterfaceAlias',
                    'netsh interface show interface'
                ]
            })
            
        elif 'user' in task_lower or 'account' in task_lower:
            suggestions['approaches'].append({
                'method': 'PowerShell',
                'commands': [
                    'Get-LocalUser | Select-Object Name, Enabled, LastLogon',
                    'New-LocalUser -Name "UserName" -Password $Password',
                    'Add-LocalGroupMember -Group "Administrators" -Member "UserName"'
                ]
            })
            
        else:
            # Generic automation suggestions
            suggestions['approaches'].append({
                'method': 'PowerShell',
                'commands': [
                    f'# For task: {task}',
                    '# Use Get-Command *keyword* to find relevant cmdlets',
                    '# Use Get-Help cmdlet-name -Examples for usage'
                ]
            })
            
        # Always suggest Admin Center for GUI tasks
        if any(word in task_lower for word in ['click', 'button', 'window', 'gui', 'visual']):
            suggestions['approaches'].append({
                'method': 'Windows Admin Center',
                'note': 'GUI operations require Windows Admin Center or remote management'
            })
            
        return suggestions
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get Server Core system information"""
        info = {
            'type': 'Windows Server Core',
            'capabilities': {
                'screenshot': False,
                'gui': False,
                'powershell': True,
                'cmd': True,
                'wmi': True,
                'remote_management': True
            },
            'management_options': [
                'PowerShell (local and remote)',
                'Windows Admin Center (WAC)',
                'Server Manager (remote)',
                'Command Prompt',
                'WMI/CIM',
                'Remote Desktop Services (command-line)',
                'RSAT from Windows client'
            ]
        }
        
        # Try to get actual system info
        try:
            import subprocess
            
            # Get Windows version
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Caption='):
                        info['version'] = line.split('=', 1)[1].strip()
                        
        except Exception as e:
            logger.debug(f"Failed to get system info: {e}")
            
        return info