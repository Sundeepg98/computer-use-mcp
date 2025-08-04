#!/usr/bin/env python3
"""
Main integration module for computer use with Claude system
Connects visual mode, ultrathink, and safety checks
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional
from .visual_mode import VisualMode
from .safety_checks import SafetyChecker
from .visual_analyzer import VisualAnalyzer
from .computer_use_core import ComputerUseCore

logger = logging.getLogger(__name__)


class ClaudeComputerUse:
    """Main integration class for Claude with computer use"""
    
    def __init__(self):
        """Initialize Claude computer use integration"""
        self.visual_mode = VisualMode()
        self.safety = SafetyChecker()
        self.ultrathink = VisualAnalyzer()
        self.computer = ComputerUseCore()
        self.claude_executable = '/usr/local/bin/claude'
        self._check_availability()
    
    def _check_availability(self):
        """Check if computer use is available"""
        self.display_available = bool(os.environ.get('DISPLAY'))
        self.claude_available = os.path.exists(self.claude_executable)
        
        if not self.display_available:
            logger.warning("No display available - visual mode limited")
        
        if not self.claude_available:
            logger.warning(f"Claude executable not found at {self.claude_executable}")
    
    def is_available(self) -> bool:
        """Check if computer use is available"""
        return self.display_available or self.claude_available
    
    def route_command(self, command: str) -> str:
        """Route command to appropriate handler"""
        command = command.strip()
        
        # Check for visual commands
        if command.startswith('@'):
            return 'visual'
        # Check for slash commands
        elif command.startswith('/'):
            return 'command'
        # Regular text prompt
        else:
            return 'text'
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process command with appropriate handler"""
        route = self.route_command(command)
        
        # Always append ultrathink (unless it's a slash command)
        if route != 'command' and 'ultrathink' not in command:
            command = f"{command} ultrathink"
        
        if route == 'visual':
            return self.execute_visual(command)
        elif route == 'command':
            return self.execute_claude_command(command)
        else:
            return self.execute_claude_prompt(command)
    
    def execute_visual(self, command: str) -> Dict[str, Any]:
        """Execute visual command"""
        # Safety check first
        try:
            self.safety.validate_action(command)
        except Exception as e:
            raise Exception(f"BLOCKED: {e}")
        
        # Execute through visual mode
        result = self.visual_mode.execute(command)
        
        # Add ultrathink analysis
        if result.get('success'):
            result['ultrathink_analysis'] = self.ultrathink.generate_report()
        
        return result
    
    def execute_claude_command(self, command: str) -> Dict[str, Any]:
        """Execute Claude slash command"""
        try:
            result = subprocess.run(
                [self.claude_executable, command],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_claude_prompt(self, prompt: str) -> Dict[str, Any]:
        """Execute regular Claude prompt"""
        try:
            # Use --print mode for non-interactive execution
            result = subprocess.run(
                [self.claude_executable, '--print', prompt],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Prompt timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_visual_session(self) -> 'VisualSession':
        """Create a new visual session"""
        return VisualSession(self)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of computer use system"""
        return {
            'display_available': self.display_available,
            'claude_available': self.claude_available,
            'visual_mode_ready': self.visual_mode is not None,
            'safety_active': self.safety is not None,
            'ultrathink_enabled': self.ultrathink is not None,
            'safety_report': self.safety.get_safety_report(),
            'ultrathink_report': self.ultrathink.generate_report()
        }


class VisualSession:
    """A visual interaction session"""
    
    def __init__(self, claude_computer: ClaudeComputerUse):
        """Initialize visual session"""
        self.claude = claude_computer
        self.history = []
        self.context = {}
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute command in session context"""
        # Add to history
        self.history.append({
            'command': command,
            'timestamp': __import__('time').time()
        })
        
        # Execute through main system
        result = self.claude.process_command(command)
        
        # Store result in history
        self.history[-1]['result'] = result
        
        # Update context if screenshot
        if '@screen' in command and result.get('success'):
            self.context['last_screenshot'] = result
        
        return result
    
    def get_history(self) -> list:
        """Get session history"""
        return self.history
    
    def clear_history(self):
        """Clear session history"""
        self.history = []
        self.context = {}


# Convenience function for direct use
def create_claude_visual():
    """Create and return Claude computer use instance"""
    return ClaudeComputerUse()