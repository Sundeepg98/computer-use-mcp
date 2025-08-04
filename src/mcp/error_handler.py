#!/usr/bin/env python3
"""
Error handling for computer use operations
Provides recovery strategies and fallback options
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ComputerUseErrorHandler:
    """Error handler for computer use operations"""
    
    def __init__(self):
        """Initialize error handler"""
        self.error_history = []
        self.retry_limits = {
            'screenshot': 3,
            'click': 5,
            'type': 3,
            'key_press': 3
        }
        self.retry_counts = {}
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """General error handler"""
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'context': context,
            'timestamp': __import__('time').time()
        }
        
        self.error_history.append(error_info)
        
        # Determine error type and handle appropriately
        if 'screenshot' in str(context).lower():
            return self.handle_screenshot_error(error)
        elif 'click' in str(context).lower():
            return self.handle_click_error(error, 
                                           context.get('x', 0), 
                                           context.get('y', 0))
        elif 'type' in str(context).lower():
            return self.handle_type_error(error)
        else:
            return self.handle_generic_error(error)
    
    def handle_screenshot_error(self, error: Exception) -> Dict[str, Any]:
        """Handle screenshot capture errors"""
        logger.error(f"Screenshot error: {error}")
        
        response = {
            'success': False,
            'error': str(error),
            'fallback': 'text_mode'
        }
        
        # Determine fallback based on error type
        if 'display' in str(error).lower():
            response['suggestion'] = "No display available. Using text-only mode."
            response['recovery'] = "Set up X server or use WSL2 with X forwarding"
        elif 'permission' in str(error).lower():
            response['suggestion'] = "Permission denied. Check display access."
            response['recovery'] = "Run with appropriate permissions or check DISPLAY variable"
        else:
            response['suggestion'] = "Screenshot failed. Falling back to text description."
        
        return response
    
    def handle_click_error(self, error: Exception, x: int, y: int) -> Dict[str, Any]:
        """Handle click action errors"""
        logger.error(f"Click error at ({x}, {y}): {error}")
        
        action_key = f"click_{x}_{y}"
        self.retry_counts[action_key] = self.retry_counts.get(action_key, 0) + 1
        
        response = {
            'success': False,
            'error': str(error),
            'coordinates': (x, y),
            'retry': self.retry_counts[action_key] < self.retry_limits['click']
        }
        
        # Provide alternatives
        if 'not found' in str(error).lower():
            response['alternative'] = {
                'action': 'search_element',
                'suggestion': 'Element may have moved. Try screenshot first.'
            }
        elif 'timeout' in str(error).lower():
            response['alternative'] = {
                'action': 'wait_and_retry',
                'suggestion': 'Page may be loading. Wait and retry.'
            }
        else:
            response['alternative'] = {
                'action': 'keyboard_navigation',
                'suggestion': 'Try Tab key to navigate to element.'
            }
        
        return response
    
    def handle_type_error(self, error: Exception) -> Dict[str, Any]:
        """Handle text typing errors"""
        logger.error(f"Type error: {error}")
        
        response = {
            'success': False,
            'error': str(error)
        }
        
        if 'focus' in str(error).lower():
            response['suggestion'] = "No input field focused. Click on field first."
            response['recovery'] = {'action': 'click_then_type'}
        elif 'clipboard' in str(error).lower():
            response['suggestion'] = "Clipboard access failed. Type character by character."
            response['recovery'] = {'action': 'character_input'}
        else:
            response['suggestion'] = "Typing failed. Try alternative input method."
            response['recovery'] = {'action': 'paste_text'}
        
        return response
    
    def handle_safety_violation(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """Handle safety check violations"""
        logger.warning(f"Safety violation: {violation}")
        
        response = {
            'blocked': True,
            'reason': violation.get('reason', 'Safety check failed'),
            'action': violation.get('action', 'unknown')
        }
        
        # Provide safe alternatives
        if 'delete' in str(violation).lower():
            response['suggestion'] = "Instead of deleting, consider moving to trash or archiving"
        elif 'password' in str(violation).lower():
            response['suggestion'] = "Never automate password entry. Use secure credential manager."
        elif 'sensitive' in str(violation).lower():
            response['suggestion'] = "Sensitive data detected. Mask or redact before proceeding."
        else:
            response['suggestion'] = "Action blocked for safety. Review and modify command."
        
        self.error_history.append({
            'type': 'safety_violation',
            'violation': violation,
            'response': response,
            'timestamp': __import__('time').time()
        })
        
        return response
    
    def handle_generic_error(self, error: Exception) -> Dict[str, Any]:
        """Handle generic/unknown errors"""
        logger.error(f"Generic error: {error}")
        
        return {
            'success': False,
            'error': str(error),
            'type': 'generic',
            'suggestion': 'Unexpected error occurred. Check logs for details.',
            'recovery': 'Retry with modified parameters or report issue'
        }
    
    def get_retry_suggestion(self, action: str) -> Optional[Dict[str, Any]]:
        """Get retry suggestion for failed action"""
        if action not in self.retry_limits:
            return None
        
        current_retries = self.retry_counts.get(action, 0)
        max_retries = self.retry_limits[action]
        
        if current_retries >= max_retries:
            return {
                'retry': False,
                'reason': 'Max retries exceeded',
                'suggestion': 'Try alternative approach'
            }
        
        return {
            'retry': True,
            'attempt': current_retries + 1,
            'max_attempts': max_retries,
            'suggestion': f'Retry {current_retries + 1}/{max_retries}'
        }
    
    def reset_retry_count(self, action: str):
        """Reset retry count for action"""
        if action in self.retry_counts:
            del self.retry_counts[action]
    
    def get_error_report(self) -> Dict[str, Any]:
        """Get error statistics report"""
        error_types = {}
        for error in self.error_history:
            error_type = error.get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'recent_errors': self.error_history[-5:] if self.error_history else [],
            'retry_counts': self.retry_counts
        }
    
    def clear_history(self):
        """Clear error history"""
        self.error_history = []
        self.retry_counts = {}