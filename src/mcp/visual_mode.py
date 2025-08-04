#!/usr/bin/env python3
"""
Visual mode for claudeu - handles visual commands
Integrates computer use with Claude's interactive mode
"""

import logging
import re
from typing import Dict, Any, List, Optional
from .computer_use_core import ComputerUseCore
from .safety_checks import SafetyChecker
from .visual_analyzer import VisualAnalyzer

logger = logging.getLogger(__name__)


class VisualMode:
    """Visual mode handler for Claude"""
    
    def __init__(self):
        """Initialize visual mode"""
        self.computer = ComputerUseCore()
        self.safety = SafetyChecker()
        self.ultrathink = VisualAnalyzer()
        self.command_prefix = '@'
        self.modes = {
            'screen': 'screenshot',
            'click': 'click',
            'type': 'type',
            'automate': 'automate',
            'scroll': 'scroll',
            'drag': 'drag',
            'key': 'key_press'
        }
    
    def parse_command(self, command: str) -> Optional[str]:
        """Parse command to determine if it's a visual command"""
        if not command.startswith(self.command_prefix):
            return None
        
        # Extract mode from command
        parts = command[1:].split(None, 1)
        if not parts:
            return None
        
        mode = parts[0].lower()
        return self.modes.get(mode)
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute visual command"""
        mode = self.parse_command(command)
        
        if not mode:
            return {'success': False, 'error': 'Not a visual command'}
        
        # Extract arguments after mode
        args = command.split(None, 1)[1] if len(command.split(None, 1)) > 1 else ""
        
        # Safety check
        try:
            self.safety.validate_action(command)
        except Exception as e:
            return {'success': False, 'error': str(e), 'blocked': True}
        
        # Execute based on mode
        if mode == 'screenshot':
            return self._execute_screenshot(args)
        elif mode == 'click':
            return self._execute_click(args)
        elif mode == 'type':
            return self._execute_type(args)
        elif mode == 'automate':
            return self._execute_automation(args)
        elif mode == 'scroll':
            return self._execute_scroll(args)
        elif mode == 'drag':
            return self._execute_drag(args)
        elif mode == 'key_press':
            return self._execute_key(args)
        else:
            return {'success': False, 'error': f'Unknown mode: {mode}'}
    
    def _execute_screenshot(self, args: str) -> Dict[str, Any]:
        """Execute screenshot command"""
        try:
            screenshot = self.computer.screenshot()
            analysis = self.ultrathink.analyze_visual_context(screenshot)
            
            return {
                'success': True,
                'mode': 'screenshot',
                'analysis': analysis,
                'query': args
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_click(self, args: str) -> Dict[str, Any]:
        """Execute click command"""
        # Parse click target from args
        # Could be coordinates or element description
        match = re.search(r'(\d+),?\s*(\d+)', args)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            return self.computer.click(x, y)
        else:
            # Would need element detection for text-based targets
            return {
                'success': False,
                'error': 'Click target not recognized',
                'suggestion': 'Provide coordinates (x, y) or clear element description'
            }
    
    def _execute_type(self, args: str) -> Dict[str, Any]:
        """Execute type command"""
        if not args:
            return {'success': False, 'error': 'No text provided to type'}
        
        # Safety check content
        content_check = self.safety.check_content(args)
        if not content_check['safe']:
            args = self.safety.sanitize_text(args)
        
        return self.computer.type_text(args)
    
    def _execute_automation(self, args: str) -> Dict[str, Any]:
        """Execute automation sequence"""
        # Plan actions using ultrathink
        plan = self.ultrathink.plan_actions(args)
        
        # Execute plan
        results = self.execute_sequence(plan)
        
        return {
            'success': results['success'],
            'mode': 'automate',
            'goal': args,
            'plan': plan,
            'results': results
        }
    
    def _execute_scroll(self, args: str) -> Dict[str, Any]:
        """Execute scroll command"""
        direction = 'down'
        amount = 3
        
        if 'up' in args.lower():
            direction = 'up'
        
        # Extract amount if specified
        match = re.search(r'\d+', args)
        if match:
            amount = int(match.group())
        
        return self.computer.scroll(direction, amount)
    
    def _execute_drag(self, args: str) -> Dict[str, Any]:
        """Execute drag command"""
        # Parse start and end coordinates
        match = re.search(r'(\d+),?\s*(\d+)\s+to\s+(\d+),?\s*(\d+)', args)
        if match:
            start_x = int(match.group(1))
            start_y = int(match.group(2))
            end_x = int(match.group(3))
            end_y = int(match.group(4))
            return self.computer.drag(start_x, start_y, end_x, end_y)
        else:
            return {
                'success': False,
                'error': 'Invalid drag syntax',
                'suggestion': 'Use: @drag x1,y1 to x2,y2'
            }
    
    def _execute_key(self, args: str) -> Dict[str, Any]:
        """Execute key press command"""
        if not args:
            return {'success': False, 'error': 'No key specified'}
        
        # Map common key names
        key_map = {
            'enter': 'Return',
            'tab': 'Tab',
            'escape': 'Escape',
            'space': 'space',
            'backspace': 'BackSpace',
            'delete': 'Delete',
            'up': 'Up',
            'down': 'Down',
            'left': 'Left',
            'right': 'Right',
        }
        
        key = key_map.get(args.lower(), args)
        return self.computer.key_press(key)
    
    def execute_sequence(self, sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a sequence of actions"""
        executed = []
        
        for step in sequence:
            action = step.get('action')
            
            try:
                if action == 'screenshot':
                    result = self.computer.screenshot()
                elif action == 'click':
                    target = step.get('target', (0, 0))
                    if isinstance(target, tuple):
                        result = self.computer.click(target[0], target[1])
                    else:
                        result = {'success': False, 'error': 'Target resolution needed'}
                elif action == 'type':
                    result = self.computer.type_text(step.get('content', ''))
                elif action == 'wait':
                    result = self.computer.wait(step.get('duration', 1))
                elif action == 'key_press':
                    result = self.computer.key_press(step.get('key', 'Return'))
                else:
                    result = {'success': False, 'error': f'Unknown action: {action}'}
                
                executed.append({
                    'step': step,
                    'result': result
                })
                
                if not result.get('success', False):
                    break
                    
            except Exception as e:
                executed.append({
                    'step': step,
                    'result': {'success': False, 'error': str(e)}
                })
                break
        
        return {
            'success': all(e['result'].get('success', False) for e in executed),
            'executed': executed,
            'total_steps': len(sequence)
        }
    
    def capture_and_analyze(self, query: str) -> Dict[str, Any]:
        """Capture screenshot and analyze with query"""
        try:
            screenshot = self.computer.screenshot()
            analysis = self.ultrathink.analyze_visual_context(screenshot)
            
            # Add query-specific analysis
            analysis['query'] = query
            analysis['response'] = f"Analysis of: {query}"
            
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }