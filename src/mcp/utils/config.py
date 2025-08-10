"""
Configuration management for computer use system
Handles settings, modes, and persistence
"""

import platform as plat
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
import os

from ..core.paths import (
    TEMP_DIR, CLAUDE_CONFIG_FILE, VCXSRV_PATHS,
    X11_SOCKET, X11_LOCK_FILES, RESOLV_CONF,
    ETC_SUDOERS_DIR, ETC_SSH_CONFIG, USR_LOCAL_BINS,
    BASHRC, PROFILE, WSL_MOUNT_PREFIX,
    get_temp_dir, get_vcxsrv_installer_path
)

logger = logging.getLogger(__name__)


class ComputerUseConfig:
    """Configuration manager for computer use"""


    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration"""
        self.config_path = config_path or str(CLAUDE_CONFIG_FILE)
        self.config = self._load_config()
        self._apply_defaults()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return {}

    def _apply_defaults(self) -> None:
        """Apply default configuration values"""
        defaults = {
            'safety_checks_enabled': True,
            'mode': 'personal',
            'screen_resolution': (1920, 1080),
            'safety_rules': self._get_default_safety_rules(),
            'visual_settings': {
                'screenshot_quality': 'high',
                'ocr_enabled': False,
                'element_detection': True
            },
            'automation_settings': {
                'default_wait': 1.0,
                'retry_attempts': 3,
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'file': '~/.claude/computer_use/logs/activity.log'
            },
            'paths': {
                'temp_dir': str(TEMP_DIR),
                'temp_dir_windows': 'C:\\Temp',
                'vcxsrv_installer': str(get_vcxsrv_installer_path()),
                'vcxsrv_installer_windows': str(get_vcxsrv_installer_path()),
                'vcxsrv_program_files': [str(p) for p in VCXSRV_PATHS],
                'x11_socket': str(X11_SOCKET),
                'x11_lock_files': [str(p) for p in X11_LOCK_FILES],
                'etc_resolv_conf': str(RESOLV_CONF),
                'etc_sudoers_dir': str(ETC_SUDOERS_DIR),
                'etc_ssh_config': str(ETC_SSH_CONFIG),
                'usr_local_bins': [str(p) for p in USR_LOCAL_BINS],
                'bashrc': str(BASHRC),
                'profile': str(PROFILE),
                'config_base': '~/.claude/computer_use',
                'wsl_mount_prefix': str(WSL_MOUNT_PREFIX)
            }
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _get_default_safety_rules(self) -> List[str]:
        """Get default safety rules based on mode"""
        if self.config.get('mode') == 'personal':
            # Minimal rules for personal use
            return [
                'no_payment_buttons',
                'no_password_fields',
                'confirm_deletions'
            ]
        else:
            # Comprehensive rules for other modes
            return [
                'no_payment_buttons',
                'no_password_fields',
                'confirm_deletions',
                'no_system_files',
                'no_registry_edits',
                'no_network_config',
                'no_security_settings',
                'screenshot_sanitization',
                'audit_logging'
            ]


    @property
    def safety_checks_enabled(self) -> bool:
        """Check if safety checks are enabled"""
        return self.config.get('safety_checks_enabled', True)

    @safety_checks_enabled.setter
    def safety_checks_enabled(self, value: bool) -> None:
        """Set safety checks enabled state"""
        self.config['safety_checks_enabled'] = value

    @property
    def screen_resolution(self) -> tuple:
        """Get configured screen resolution"""
        res = self.config.get('screen_resolution', [1920, 1080])
        return tuple(res)

    @property
    def safety_rules(self) -> List[str]:
        """Get active safety rules"""
        return self.config.get('safety_rules', [])

    def set_mode(self, mode: str) -> None:
        """Set operation mode (personal, development, production)"""
        valid_modes = ['personal', 'development', 'production']

        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")

        self.config['mode'] = mode

        # Update safety rules based on mode
        if mode == 'personal':
            self.config['safety_rules'] = [
                'no_payment_buttons',
                'no_password_fields',
                'confirm_deletions'
            ]
        elif mode == 'development':
            self.config['safety_rules'] = [
                'no_payment_buttons',
                'no_password_fields',
                'confirm_deletions',
                'no_production_access',
                'sandbox_only'
            ]
        else:  # production
            self.config['safety_rules'] = self._get_default_safety_rules() + [
                'require_approval',
                'comprehensive_audit',
                'rollback_capability'
            ]

        logger.info(f"Mode set to: {mode}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value

    def save(self) -> None:
        """Save configuration to file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def load(self) -> 'ComputerUseConfig':
        """Reload configuration from file"""
        self.config = self._load_config()
        self._apply_defaults()
        return self

    def reset(self) -> None:
        """Reset configuration to defaults"""
        self.config = {}
        self._apply_defaults()
        logger.info("Configuration reset to defaults")

    def export(self, path: str) -> None:
        """Export configuration to specified path"""
        try:
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration exported to {path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")

    def import_config(self, path: str) -> None:
        """Import configuration from specified path"""
        try:
            with open(path, 'r') as f:
                imported = json.load(f)

            # Validate imported config
            if not isinstance(imported, dict):
                raise ValueError("Invalid configuration format")

            self.config.update(imported)
            logger.info(f"Configuration imported from {path}")
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get configuration status"""
        return {
            'mode': self.config.get('mode'),
            'safety_checks_enabled': self.safety_checks_enabled,
            'safety_rules_count': len(self.safety_rules),
            'config_path': self.config_path,
            'config_exists': os.path.exists(self.config_path)
        }

    def validate(self) -> bool:
        """Validate configuration"""
        required_keys = ['mode', 'safety_checks_enabled']

        for key in required_keys:
            if key not in self.config:
                logger.error(f"Missing required configuration key: {key}")
                return False

        return True

    def get_path(self, path_key: str, expand: bool = True) -> str:
        """Get a configured path"""
        paths = self.config.get('paths', {})
        path = paths.get(path_key, '')

        if expand and path and path.startswith('~'):
            return os.path.expanduser(path)
        return path

    def get_paths(self, path_key: str) -> List[str]:
        """Get a list of configured paths"""
        paths = self.config.get('paths', {})
        path_list = paths.get(path_key, [])

        if isinstance(path_list, str):
            path_list = [path_list]

        return [os.path.expanduser(p) if p.startswith('~') else p for p in path_list]

    def get_platform_path(self, path_key: str, platform: Optional[str] = None) -> str:
        """Get platform-specific path"""

        if platform is None:
            platform = 'windows' if plat.system() == 'Windows' else 'linux'

        # Try platform-specific key first
        platform_key = f"{path_key}_{platform}"
        path = self.get_path(platform_key)

        # Fall back to generic key
        if not path:
            path = self.get_path(path_key)

        return path