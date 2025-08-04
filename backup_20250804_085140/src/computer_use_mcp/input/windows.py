"""
Windows input implementation for mouse and keyboard operations
Supports native Windows and WSL2 environments
"""

import os
import sys
import subprocess
import time
import logging
from typing import Dict, Any, Tuple, Optional, List
from ..safety_checks import SafetyChecker

logger = logging.getLogger(__name__)


class WindowsInput:
    """Native Windows input using ctypes"""
    
    def __init__(self):
        self.safety_checker = SafetyChecker()
        self._import_windows_libs()
    
    def _import_windows_libs(self):
        """Import Windows-specific libraries"""
        if sys.platform != 'win32':
            raise ImportError("WindowsInput requires Windows platform")
        
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        self.user32 = ctypes.windll.user32
        
        # Define constants
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_MIDDLEDOWN = 0x0020
        self.MOUSEEVENTF_MIDDLEUP = 0x0040
        self.MOUSEEVENTF_WHEEL = 0x0800
        self.MOUSEEVENTF_ABSOLUTE = 0x8000
        
        # Input structures
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
        
        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
            _anonymous_ = ("_input",)
            _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]
        
        self.MOUSEINPUT = MOUSEINPUT
        self.KEYBDINPUT = KEYBDINPUT
        self.INPUT = INPUT
        self.INPUT_MOUSE = 0
        self.INPUT_KEYBOARD = 1
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform mouse click at coordinates"""
        # Validate coordinates
        self._validate_coordinates(x, y)
        
        # Move mouse
        self.user32.SetCursorPos(x, y)
        
        # Determine button flags
        if button == 'left':
            down_flag = self.MOUSEEVENTF_LEFTDOWN
            up_flag = self.MOUSEEVENTF_LEFTUP
        elif button == 'right':
            down_flag = self.MOUSEEVENTF_RIGHTDOWN
            up_flag = self.MOUSEEVENTF_RIGHTUP
        elif button == 'middle':
            down_flag = self.MOUSEEVENTF_MIDDLEDOWN
            up_flag = self.MOUSEEVENTF_MIDDLEUP
        else:
            raise ValueError(f"Invalid button: {button}")
        
        # Click
        self.user32.mouse_event(down_flag, 0, 0, 0, 0)
        time.sleep(0.01)  # Small delay
        self.user32.mouse_event(up_flag, 0, 0, 0, 0)
        
        return {
            'success': True,
            'action': 'click',
            'coordinates': (x, y),
            'button': button,
            'timestamp': time.time()
        }
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to coordinates without clicking"""
        self._validate_coordinates(x, y)
        
        self.user32.SetCursorPos(x, y)
        
        return {
            'success': True,
            'action': 'move',
            'coordinates': (x, y),
            'timestamp': time.time()
        }
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Click and drag from start to end coordinates"""
        self._validate_coordinates(start_x, start_y)
        self._validate_coordinates(end_x, end_y)
        
        # Move to start
        self.user32.SetCursorPos(start_x, start_y)
        time.sleep(0.05)
        
        # Mouse down
        self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        
        # Move to end
        self.user32.SetCursorPos(end_x, end_y)
        time.sleep(0.05)
        
        # Mouse up
        self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        return {
            'success': True,
            'action': 'drag',
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'timestamp': time.time()
        }
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll in specified direction"""
        # Wheel delta (positive = up, negative = down)
        wheel_delta = -120 if direction == 'down' else 120
        
        for _ in range(amount):
            self.user32.mouse_event(self.MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)
            time.sleep(0.05)
        
        return {
            'success': True,
            'action': 'scroll',
            'direction': direction,
            'amount': amount,
            'timestamp': time.time()
        }
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        point = self.wintypes.POINT()
        self.user32.GetCursorPos(self.ctypes.byref(point))
        return (point.x, point.y)
    
    def _validate_coordinates(self, x: int, y: int):
        """Validate mouse coordinates"""
        if x < 0 or y < 0:
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        # Check screen bounds
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            max_x = max(m.x + m.width for m in monitors)
            max_y = max(m.y + m.height for m in monitors)
            
            if x >= max_x or y >= max_y:
                raise ValueError(f"Coordinates ({x}, {y}) beyond screen bounds")
        except ImportError:
            # If screeninfo not available, just check reasonable bounds
            if x > 5000 or y > 5000:
                logger.warning(f"Coordinates ({x}, {y}) seem unusually large")


class WindowsKeyboard:
    """Native Windows keyboard input"""
    
    def __init__(self):
        self.safety_checker = SafetyChecker()
        self._import_windows_libs()
        self._setup_key_codes()
    
    def _import_windows_libs(self):
        """Import Windows libraries"""
        if sys.platform != 'win32':
            raise ImportError("WindowsKeyboard requires Windows platform")
        
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        self.user32 = ctypes.windll.user32
        
        # Import structures (reuse from WindowsInput)
        from .windows import WindowsInput
        win_input = WindowsInput()
        self.INPUT = win_input.INPUT
        self.KEYBDINPUT = win_input.KEYBDINPUT
        self.INPUT_KEYBOARD = win_input.INPUT_KEYBOARD
        
        # Key event flags
        self.KEYEVENTF_KEYUP = 0x0002
        self.KEYEVENTF_UNICODE = 0x0004
    
    def _setup_key_codes(self):
        """Setup virtual key codes"""
        self.VK_CODES = {
            'Return': 0x0D,
            'Tab': 0x09,
            'Escape': 0x1B,
            'Space': 0x20,
            'BackSpace': 0x08,
            'Delete': 0x2E,
            'Up': 0x26,
            'Down': 0x28,
            'Left': 0x25,
            'Right': 0x27,
            'Home': 0x24,
            'End': 0x23,
            'Page_Up': 0x21,
            'Page_Down': 0x22,
            'ctrl': 0x11,
            'alt': 0x12,
            'shift': 0x10,
            'cmd': 0x5B,  # Windows key
            'F1': 0x70,
            'F2': 0x71,
            'F3': 0x72,
            'F4': 0x73,
            'F5': 0x74,
            'F6': 0x75,
            'F7': 0x76,
            'F8': 0x77,
            'F9': 0x78,
            'F10': 0x79,
            'F11': 0x7A,
            'F12': 0x7B,
        }
        
        # Add letters and numbers
        for i in range(26):
            self.VK_CODES[chr(ord('a') + i)] = 0x41 + i
            self.VK_CODES[chr(ord('A') + i)] = 0x41 + i
        
        for i in range(10):
            self.VK_CODES[str(i)] = 0x30 + i
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text using keyboard"""
        # Safety check
        if not self.safety_checker.check_text_safety(text):
            raise Exception(f"Safety check failed: {self.safety_checker.last_error}")
        
        inputs = []
        
        for char in text:
            # Use Unicode input for all characters
            input_down = self.INPUT()
            input_down.type = self.INPUT_KEYBOARD
            input_down.ki.wScan = ord(char)
            input_down.ki.dwFlags = self.KEYEVENTF_UNICODE
            inputs.append(input_down)
            
            input_up = self.INPUT()
            input_up.type = self.INPUT_KEYBOARD
            input_up.ki.wScan = ord(char)
            input_up.ki.dwFlags = self.KEYEVENTF_UNICODE | self.KEYEVENTF_KEYUP
            inputs.append(input_up)
        
        # Send all inputs
        n_inputs = len(inputs)
        array_type = self.INPUT * n_inputs
        input_array = array_type(*inputs)
        
        self.user32.SendInput(n_inputs, input_array, self.ctypes.sizeof(self.INPUT))
        
        return {
            'success': True,
            'action': 'type',
            'text': text,
            'length': len(text),
            'timestamp': time.time()
        }
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press a specific key or key combination"""
        keys = key.split('+')
        pressed_keys = []
        
        try:
            # Press all keys down
            for k in keys:
                k = k.strip()
                if k in self.VK_CODES:
                    vk_code = self.VK_CODES[k]
                    self._key_down(vk_code)
                    pressed_keys.append(vk_code)
                else:
                    # Try as single character
                    if len(k) == 1:
                        vk_code = ord(k.upper())
                        self._key_down(vk_code)
                        pressed_keys.append(vk_code)
                    else:
                        raise ValueError(f"Unknown key: {k}")
            
            # Release all keys in reverse order
            for vk_code in reversed(pressed_keys):
                self._key_up(vk_code)
            
            return {
                'success': True,
                'action': 'key_press',
                'key': key,
                'timestamp': time.time()
            }
            
        except Exception as e:
            # Try to release any pressed keys
            for vk_code in pressed_keys:
                try:
                    self._key_up(vk_code)
                except:
                    pass
            raise e
    
    def _key_down(self, vk_code: int):
        """Send key down event"""
        input_struct = self.INPUT()
        input_struct.type = self.INPUT_KEYBOARD
        input_struct.ki.wVk = vk_code
        self.user32.SendInput(1, self.ctypes.byref(input_struct), self.ctypes.sizeof(self.INPUT))
    
    def _key_up(self, vk_code: int):
        """Send key up event"""
        input_struct = self.INPUT()
        input_struct.type = self.INPUT_KEYBOARD
        input_struct.ki.wVk = vk_code
        input_struct.ki.dwFlags = self.KEYEVENTF_KEYUP
        self.user32.SendInput(1, self.ctypes.byref(input_struct), self.ctypes.sizeof(self.INPUT))


class WSL2Input:
    """WSL2 input using PowerShell"""
    
    def __init__(self):
        self.safety_checker = SafetyChecker()
    
    def click(self, x: int, y: int, button: str = 'left') -> Dict[str, Any]:
        """Perform mouse click via PowerShell"""
        # Map button names to mouse button codes
        button_map = {
            'left': 'Left',
            'right': 'Right',
            'middle': 'Middle'
        }
        button_code = button_map.get(button, 'Left')
        
        ps_script = f'''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class MouseOperations
        {{
            [DllImport("user32.dll")]
            public static extern bool SetCursorPos(int X, int Y);
            
            [DllImport("user32.dll")]
            public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
            
            public const int MOUSEEVENTF_LEFTDOWN = 0x02;
            public const int MOUSEEVENTF_LEFTUP = 0x04;
            public const int MOUSEEVENTF_RIGHTDOWN = 0x08;
            public const int MOUSEEVENTF_RIGHTUP = 0x10;
            public const int MOUSEEVENTF_MIDDLEDOWN = 0x20;
            public const int MOUSEEVENTF_MIDDLEUP = 0x40;
        }}
"@
        
        [MouseOperations]::SetCursorPos({x}, {y})
        Start-Sleep -Milliseconds 10
        
        $buttonDown = 0
        $buttonUp = 0
        
        switch("{button_code}") {{
            "Left" {{ $buttonDown = 0x02; $buttonUp = 0x04 }}
            "Right" {{ $buttonDown = 0x08; $buttonUp = 0x10 }}
            "Middle" {{ $buttonDown = 0x20; $buttonUp = 0x40 }}
        }}
        
        [MouseOperations]::mouse_event($buttonDown, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 10
        [MouseOperations]::mouse_event($buttonUp, 0, 0, 0, 0)
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell click failed: {result.stderr.decode()}")
        
        return {
            'success': True,
            'action': 'click',
            'coordinates': (x, y),
            'button': button,
            'timestamp': time.time()
        }
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text via PowerShell"""
        # Safety check
        if not self.safety_checker.check_text_safety(text):
            raise Exception(f"Safety check failed: {self.safety_checker.last_error}")
        
        # Escape special characters for SendKeys
        escaped_text = text.replace('{', '{{').replace('}', '}}')
        escaped_text = escaped_text.replace('+', '{+}').replace('^', '{^}')
        escaped_text = escaped_text.replace('%', '{%}').replace('~', '{~}')
        escaped_text = escaped_text.replace('(', '{(}').replace(')', '{)}')
        
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.SendKeys]::SendWait("{escaped_text}")
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell type failed: {result.stderr.decode()}")
        
        return {
            'success': True,
            'action': 'type',
            'text': text,
            'length': len(text),
            'timestamp': time.time()
        }
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse via PowerShell"""
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell move failed: {result.stderr.decode()}")
        
        return {
            'success': True,
            'action': 'move',
            'coordinates': (x, y),
            'timestamp': time.time()
        }
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Drag via PowerShell"""
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({start_x}, {start_y})
        [System.Windows.Forms.SendKeys]::SendWait("{{LeftDown}}")
        Start-Sleep -Milliseconds 50
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({end_x}, {end_y})
        Start-Sleep -Milliseconds 50
        [System.Windows.Forms.SendKeys]::SendWait("{{LeftUp}}")
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell drag failed: {result.stderr.decode()}")
        
        return {
            'success': True,
            'action': 'drag',
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'timestamp': time.time()
        }
    
    def scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll via PowerShell"""
        # PowerShell doesn't have direct scroll, use SendKeys
        key = '{PGDN}' if direction == 'down' else '{PGUP}'
        
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        for ($i = 0; $i -lt {amount}; $i++) {{
            [System.Windows.Forms.SendKeys]::SendWait("{key}")
            Start-Sleep -Milliseconds 50
        }}
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        return {
            'success': result.returncode == 0,
            'action': 'scroll',
            'direction': direction,
            'amount': amount,
            'timestamp': time.time()
        }
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get mouse position via PowerShell"""
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        $pos = [System.Windows.Forms.Cursor]::Position
        Write-Output "$($pos.X),$($pos.Y)"
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            x, y = map(int, result.stdout.strip().split(','))
            return (x, y)
        
        return (0, 0)
    
    def key_press(self, key: str) -> Dict[str, Any]:
        """Press a key or key combination via PowerShell"""
        # Parse key combination
        keys = key.split('+')
        
        # Map special keys
        key_map = {
            'Return': '{ENTER}',
            'Tab': '{TAB}',
            'Escape': '{ESC}',
            'Space': ' ',
            'BackSpace': '{BACKSPACE}',
            'Delete': '{DELETE}',
            'Up': '{UP}',
            'Down': '{DOWN}',
            'Left': '{LEFT}',
            'Right': '{RIGHT}',
            'Home': '{HOME}',
            'End': '{END}',
            'Page_Up': '{PGUP}',
            'Page_Down': '{PGDN}',
            'ctrl': '^',
            'alt': '%',
            'shift': '+',
            'cmd': '^{ESC}',  # Windows key
        }
        
        # Build SendKeys string
        sendkeys_str = ''
        for k in keys:
            k = k.strip()
            if k in key_map:
                sendkeys_str += key_map[k]
            else:
                sendkeys_str += k.lower()
        
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.SendKeys]::SendWait("{sendkeys_str}")
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell key press failed: {result.stderr.decode()}")
        
        return {
            'success': True,
            'action': 'key_press',
            'key': key,
            'timestamp': time.time()
        }


class WindowsWindowManager:
    """Windows window management"""
    
    def __init__(self):
        if sys.platform != 'win32':
            # For WSL2, use PowerShell
            self.use_powershell = True
        else:
            self.use_powershell = False
            self._import_windows_libs()
    
    def _import_windows_libs(self):
        """Import Windows libraries"""
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        self.user32 = ctypes.windll.user32
    
    def get_active_window(self) -> Dict[str, Any]:
        """Get active window information"""
        if self.use_powershell:
            return self._get_active_window_ps()
        
        hwnd = self.user32.GetForegroundWindow()
        
        # Get window title
        length = self.user32.GetWindowTextLengthW(hwnd) + 1
        buffer = self.ctypes.create_unicode_buffer(length)
        self.user32.GetWindowTextW(hwnd, buffer, length)
        
        return {
            'handle': hwnd,
            'title': buffer.value,
            'active': True
        }
    
    def _get_active_window_ps(self) -> Dict[str, Any]:
        """Get active window via PowerShell"""
        ps_script = '''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {
            [DllImport("user32.dll")]
            public static extern IntPtr GetForegroundWindow();
            [DllImport("user32.dll")]
            public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
        }
"@
        $hwnd = [Win32]::GetForegroundWindow()
        $title = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $title, 256)
        @{Handle=$hwnd; Title=$title.ToString()} | ConvertTo-Json
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return {
                'handle': data['Handle'],
                'title': data['Title'],
                'active': True
            }
        
        return {'error': 'Failed to get active window'}
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """List all windows"""
        windows = []
        
        def enum_callback(hwnd, _):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd) + 1
                buffer = self.ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(hwnd, buffer, length)
                
                if buffer.value:  # Only include windows with titles
                    windows.append({
                        'handle': hwnd,
                        'title': buffer.value,
                        'visible': True
                    })
            return True
        
        # EnumWindows
        enum_func = self.ctypes.WINFUNCTYPE(
            self.ctypes.c_bool,
            self.wintypes.HWND,
            self.wintypes.LPARAM
        )(enum_callback)
        
        self.user32.EnumWindows(enum_func, 0)
        
        return windows
    
    def focus_window(self, window_handle: int) -> Dict[str, Any]:
        """Bring window to focus"""
        if self.use_powershell:
            return self._focus_window_ps(window_handle)
        
        success = self.user32.SetForegroundWindow(window_handle)
        
        return {
            'success': bool(success),
            'action': 'focus',
            'handle': window_handle
        }
    
    def _focus_window_ps(self, window_handle: int) -> Dict[str, Any]:
        """Focus window via PowerShell"""
        ps_script = f'''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {{
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
        }}
"@
        [Win32]::SetForegroundWindow([IntPtr]{window_handle})
        '''
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-Command', ps_script],
            capture_output=True,
            timeout=5
        )
        
        return {
            'success': result.returncode == 0,
            'action': 'focus',
            'handle': window_handle
        }