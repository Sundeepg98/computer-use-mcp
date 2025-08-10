"""
ValidationHandler - Handles parameter validation for MCP tools

Extracted from mcp_server.py to follow Single Responsibility Principle.
Centralizes validation logic for tool parameters.
"""

from typing import Dict, Any, Optional, Tuple, List, Set
import logging


logger = logging.getLogger(__name__)


class ValidationHandler:
    """Handles validation for MCP tool parameters"""


    def __init__(self) -> None:
        """Initialize validation handler with rules"""
        self.validation_rules = self._init_validation_rules()
        self._valid_keys = self._init_valid_keys()
        self._key_aliases = self._init_key_aliases()

def _init_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules for each tool"""
        return {
            'screenshot': {
                'optional': ['method', 'save_path'],
                'valid_methods': [
                    'windows_native', 'windows_rdp_capture',
                    'wsl2_powershell', 'x11', 'vcxsrv_x11',
                    'server_core', 'macos_screencapture', 'recommended'
                ]
            },
            'click': {
                'required_one_of': [['x', 'y'], ['element']],
                'types': {'x': int, 'y': int, 'button': str},
                'valid_buttons': ['left', 'right', 'middle']
            },
            'type': {
                'required': ['text'],
                'types': {'text': str}
            },
            'key': {
                'required': ['key'],
                'types': {'key': str}
            },
            'scroll': {
                'optional': ['direction', 'amount'],
                'types': {'direction': str, 'amount': int},
                'valid_directions': ['up', 'down']
            },
            'drag': {
                'required': ['start_x', 'start_y', 'end_x', 'end_y'],
                'types': {
                    'start_x': int, 'start_y': int,
                    'end_x': int, 'end_y': int
                }
            },
            'wait': {
                'optional': ['seconds'],
                'types': {'seconds': (int, float)}
            },
            'get_platform_info': {},
            'check_display_available': {}
        }

def _init_valid_keys(self) -> Set[str]:
        """Initialize set of valid keyboard keys"""
        return {
            # Special keys
            'Return', 'Tab', 'Escape', 'BackSpace', 'Delete', 'Insert',
            'Up', 'Down', 'Left', 'Right', 'Home', 'End',
            'Page_Up', 'Page_Down', 'space',

            # Function keys
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
            'F7', 'F8', 'F9', 'F10', 'F11', 'F12',

            # Modifiers
            'Ctrl', 'Alt', 'Shift', 'Super', 'Meta', 'Cmd',

            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
            'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
            'U', 'V', 'W', 'X', 'Y', 'Z',

            # Numbers
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',

            # Common symbols
            'plus', 'minus', 'equal', 'underscore', 'period', 'comma',
            'slash', 'backslash', 'semicolon', 'apostrophe',
            'bracketleft', 'bracketright'
        }

def _init_key_aliases(self) -> Dict[str, str]:
        """Initialize key name aliases for normalization"""
        return {
            'enter': 'Return',
            'return': 'Return',
            'esc': 'Escape',
            'escape': 'Escape',
            'backspace': 'BackSpace',
            'delete': 'Delete',
            'del': 'Delete',
            'ins': 'Insert',
            'insert': 'Insert',
            'pageup': 'Page_Up',
            'pagedown': 'Page_Down',
            'pgup': 'Page_Up',
            'pgdn': 'Page_Down',
            'space': 'space',
            ' ': 'space',
            'ctrl': 'Ctrl',
            'control': 'Ctrl',
            'alt': 'Alt',
            'shift': 'Shift',
            'cmd': 'Cmd',
            'command': 'Cmd',
            'win': 'Super',
            'windows': 'Super',
            'meta': 'Meta'
        }

def validate_tool_params(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters for a specific tool

        Args:
            tool_name: Name of the tool
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        rules = self.validation_rules.get(tool_name)
        if not rules:
            return False, f"Unknown tool: {tool_name}"

        # Check required parameters
        if 'required' in rules:
            for field in rules['required']:
                if field not in params:
                    return False, f"Missing required parameter: {field}"

        # Check required one-of groups
        if 'required_one_of' in rules:
            satisfied = False
            for group in rules['required_one_of']:
                if all(field in params for field in group):
                    satisfied = True
                    break
            if not satisfied:
                groups_str = ' or '.join([str(group) for group in rules['required_one_of']])
                return False, f"Must provide one of these parameter groups: {groups_str}"

        # Check parameter types
        if 'types' in rules:
            for field, expected_type in rules['types'].items():
                if field in params:
                    value = params[field]
                    if isinstance(expected_type, tuple):
                        if not isinstance(value, expected_type):
                            return False, f"{field} must be of type {expected_type}"
                    else:
                        if not isinstance(value, expected_type):
                            return False, f"{field} must be of type {expected_type.__name__}"

        # Tool-specific validation
        if tool_name == 'screenshot':
            if 'method' in params:
                if params['method'] not in rules['valid_methods']:
                    return False, f"Invalid screenshot method: {params['method']}"

        elif tool_name == 'click':
            if 'x' in params and 'y' in params:
                is_valid, error = self.validate_coordinates(params['x'], params['y'])
                if not is_valid:
                    return False, error
            if 'button' in params:
                if params['button'] not in rules['valid_buttons']:
                    return False, f"Invalid button: {params['button']}"

        elif tool_name == 'key':
            if 'key' in params:
                is_valid, error = self._validate_key_param(params['key'])
                if not is_valid:
                    return False, error

        elif tool_name == 'scroll':
            if 'direction' in params:
                if params['direction'] not in rules['valid_directions']:
                    return False, f"Invalid scroll direction: {params['direction']}"

        elif tool_name == 'drag':
            # Validate all coordinates
            for coord in ['start_x', 'start_y', 'end_x', 'end_y']:
                if coord in params:
                    is_valid, error = self.validate_coordinates(params[coord], 0)  # Dummy y
                    if not is_valid:
                        return False, f"{coord}: {error}"

        return True, None

def validate_coordinates(self, x: Any, y: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate x,y coordinates

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(x, int) or not isinstance(y, int):
            return False, "Coordinates must be integers"

        if x < 0 or y < 0:
            return False, "Coordinates cannot be negative"

        return True, None

def _validate_key_param(self, key: str) -> Tuple[bool, Optional[str]]:
        """Validate keyboard key or combination"""
        if not isinstance(key, str):
            return False, "Key must be a string"

        # Handle key combinations (e.g., Ctrl+C)
        if '+' in key:
            parts = key.split('+')
            for part in parts:
                normalized = self.normalize_key(part)
                if normalized not in self._valid_keys:
                    return False, f"Invalid key in combination: {part}"
        else:
            normalized = self.normalize_key(key)
            if normalized not in self._valid_keys:
                return False, f"Invalid key: {key}"

        return True, None

def normalize_key(self, key: str) -> str:
        """
        Normalize key name to standard format

        Args:
            key: Key name to normalize

        Returns:
            Normalized key name
        """
        key_lower = key.lower().strip()

        # Check aliases first
        if key_lower in self._key_aliases:
            return self._key_aliases[key_lower]

        # Handle modifier combinations
        if '+' in key:
            parts = key.split('+')
            normalized_parts = []
            for part in parts:
                part_lower = part.lower().strip()
                if part_lower in self._key_aliases:
                    normalized_parts.append(self._key_aliases[part_lower])
                else:
                    # Keep original case for letters
                    if len(part) == 1 and part.isalpha():
                        normalized_parts.append(part.upper())
                    else:
                        normalized_parts.append(part)
            return '+'.join(normalized_parts)

        # Single letter keys are uppercase
        if len(key) == 1 and key.isalpha():
            return key.upper()

        # Return as-is if not found in aliases
        return key

def get_valid_keys(self) -> List[str]:
        """Get list of valid keyboard keys"""
        return sorted(list(self._valid_keys))