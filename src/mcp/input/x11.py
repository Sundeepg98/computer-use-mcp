"""
X11 input implementation for Linux
"""

import subprocess
import time
import logging
from typing import Dict, Any, Tuple
from ..safety_checks import SafetyChecker

logger = logging.getLogger(__name__)


class X11Input:
    """X11 input implementation using xdotool"""
    
    def __init__(self):
        self.safety_checker = SafetyChecker()
        self._check_xdotool()
    
    def _check_xdotool(self):
        """Check if xdotool is available"""
        try:
            subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("xdotool not found. X11 input may not work properly.")
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform mouse click at coordinates"""
        # Map button names
        button_map = {
            'left': '1',
            'middle': '2',
            'right': '3'
        }
        button_num = button_map.get(button, '1')
        
        try:
            # Move and click
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            time.sleep(0.01)
            subprocess.run(['xdotool', 'click', button_num], check=True)
            
            return {
                'success': True,
                'action': 'click',
                'coordinates': (x, y),
                'button': button,
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool click failed: {e}")
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to coordinates"""
        try:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            
            return {
                'success': True,
                'action': 'move',
                'coordinates': (x, y),
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool move failed: {e}")
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Click and drag"""
        try:
            subprocess.run(['xdotool', 'mousemove', str(start_x), str(start_y)], check=True)
            subprocess.run(['xdotool', 'mousedown', '1'], check=True)
            time.sleep(0.05)
            subprocess.run(['xdotool', 'mousemove', str(end_x), str(end_y)], check=True)
            subprocess.run(['xdotool', 'mouseup', '1'], check=True)
            
            return {
                'success': True,
                'action': 'drag',
                'start': (start_x, start_y),
                'end': (end_x, end_y),
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool drag failed: {e}")
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll mouse wheel"""
        button = '5' if direction == 'down' else '4'
        
        try:
            for _ in range(amount):
                subprocess.run(['xdotool', 'click', button], check=True)
                time.sleep(0.05)
            
            return {
                'success': True,
                'action': 'scroll',
                'direction': direction,
                'amount': amount,
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool scroll failed: {e}")
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        try:
            result = subprocess.run(
                ['xdotool', 'getmouselocation'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse output like "x:123 y:456 screen:0 window:12345"
            parts = result.stdout.split()
            x_part = next((p for p in parts if p.startswith('x:')), None)
            y_part = next((p for p in parts if p.startswith('y:')), None)
            if x_part and y_part:
                x = int(x_part.split(':')[1])
                y = int(y_part.split(':')[1])
                return (x, y)
        except Exception as e:
            logger.error(f"Get mouse position failed: {e}")
        
        return (0, 0)
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text"""
        # Safety check
        if not self.safety_checker.check_text_safety(text):
            raise Exception(f"Safety check failed: {self.safety_checker.last_error}")
        
        try:
            subprocess.run(['xdotool', 'type', '--clearmodifiers', text], check=True)
            
            return {
                'success': True,
                'action': 'type',
                'text': text,
                'length': len(text),
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool type failed: {e}")
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press key or key combination"""
        try:
            subprocess.run(['xdotool', 'key', key], check=True)
            
            return {
                'success': True,
                'action': 'key_press',
                'key': key,
                'timestamp': time.time()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"xdotool key press failed: {e}")