"""Centralized path configuration for computer-use-mcp

This module consolidates all hardcoded paths across the project into
a single configurable location.
"""
import os
from pathlib import Path
import platform


# Base paths
HOME_DIR = Path.home()
TEMP_DIR = Path("/tmp") if os.name != 'nt' else Path("C:/Temp")

# Windows paths
WINDOWS_SYSTEM32 = Path("C:/Windows/System32")
PROGRAM_FILES = Path("C:/Program Files")
PROGRAM_FILES_X86 = Path("C:/Program Files (x86)")

# VcXsrv paths
VCXSRV_PATHS = [
    PROGRAM_FILES / "VcXsrv/vcxsrv.exe",
    PROGRAM_FILES_X86 / "VcXsrv/vcxsrv.exe",
    Path("C:/VcXsrv/vcxsrv.exe"),
    Path("C:/Tools/VcXsrv/vcxsrv.exe")
]

# Unix paths
X11_SOCKET = Path("/tmp/.X11-unix")
X11_LOCK_FILES = [Path("/tmp/.X0-lock"), Path("/tmp/.X11-unix/X0")]
RESOLV_CONF = Path("/etc/resolv.conf")
ETC_SUDOERS_DIR = Path("/etc/sudoers.d")
ETC_SSH_CONFIG = Path("/etc/ssh/sshd_config")
USR_LOCAL_BINS = [Path("/usr/local/bin"), Path("/usr/local/sbin")]

# User config paths
BASHRC = HOME_DIR / ".bashrc"
PROFILE = HOME_DIR / ".profile"

# Claude paths
CLAUDE_CONFIG_DIR = HOME_DIR / ".claude/computer_use"
CLAUDE_CONFIG_FILE = CLAUDE_CONFIG_DIR / "config/settings.json"
CLAUDE_LOG_FILE = CLAUDE_CONFIG_DIR / "logs/activity.log"
CLAUDE_TEMP_DIR = CLAUDE_CONFIG_DIR / "temp"
CLAUDE_STATE_FILE = CLAUDE_CONFIG_DIR / "state.json"

# WSL mount paths
WSL_MOUNT_PREFIX = Path("/mnt/c")

# Screenshot paths
SCREENSHOT_DEFAULT_PATH = TEMP_DIR / "screenshot.png"
VCXSRV_INSTALLER_PATH = TEMP_DIR / "vcxsrv_installer.exe"

# Platform-specific temp paths
def get_temp_dir() -> Path:
    """Get platform-appropriate temp directory"""
    if platform.system() == "Windows":
        return Path("C:/Temp")
    return Path("/tmp")


def get_vcxsrv_installer_path() -> Path:
    """Get platform-appropriate VcXsrv installer path"""
    temp_dir = get_temp_dir()
    return temp_dir / "vcxsrv_installer.exe"


def get_wsl_windows_path(windows_path: str) -> Path:
    """Convert Windows path to WSL path
    
    Args:
        windows_path: Windows path like C:\\Program Files\\...
        
    Returns:
        WSL equivalent path like /mnt/c/Program Files/...
    """
    # Remove drive letter and colon
    if len(windows_path) >= 2 and windows_path[1] == ':':
        drive_letter = windows_path[0].lower()
        path_without_drive = windows_path[2:]
        # Convert backslashes to forward slashes
        path_without_drive = path_without_drive.replace('\\', '/')
        return WSL_MOUNT_PREFIX / drive_letter / path_without_drive.lstrip('/')
    return Path(windows_path)


def get_windows_path_from_wsl(wsl_path: str) -> str:
    """Convert WSL path to Windows path
    
    Args:
        wsl_path: WSL path like /mnt/c/Program Files/...
        
    Returns:
        Windows path like C:\\Program Files\\...
    """
    path = Path(wsl_path)
    
    # Check if it's a WSL mount path
    if str(path).startswith("/mnt/"):
        parts = path.parts
        if len(parts) >= 3:  # /mnt/c/...
            drive_letter = parts[2].upper()
            remaining_path = "\\".join(parts[3:])
            return f"{drive_letter}:\\{remaining_path}"
    
    return str(path)


def get_vcxsrv_search_paths() -> list[Path]:
    """Get all paths to search for VcXsrv executable"""
    paths = list(VCXSRV_PATHS)
    
    # Add WSL-converted paths if in WSL environment
    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    # In WSL, add converted Windows paths
                    for vcxsrv_path in VCXSRV_PATHS:
                        wsl_path = get_wsl_windows_path(str(vcxsrv_path))
                        if wsl_path not in paths:
                            paths.append(wsl_path)
        except IOError:
            pass
    
    return paths


def ensure_dir(path: Path, mode: int = 0o755) -> Path:
    """Ensure directory exists with proper permissions
    
    Args:
        path: Directory path to create
        mode: Unix permissions (ignored on Windows)
        
    Returns:
        The path that was created
    """
    path.mkdir(parents=True, exist_ok=True)
    
    # Set permissions on Unix-like systems
    if os.name != 'nt':
        try:
            path.chmod(mode)
        except Exception:
            pass
    
    return path


def get_secure_temp_file(prefix: str = "computer_use_", suffix: str = ".tmp") -> Path:
    """Get a secure temporary file path
    
    Args:
        prefix: File prefix
        suffix: File suffix
        
    Returns:
        Path to temporary file
    """
    import tempfile
    
    # Use Claude temp dir if available, otherwise system temp
    temp_dir = CLAUDE_TEMP_DIR if CLAUDE_TEMP_DIR.exists() else get_temp_dir()
    ensure_dir(temp_dir)
    
    # Create temp file
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=str(temp_dir))
    os.close(fd)  # Close file descriptor
    
    return Path(path)


# Protected system paths (for safety checks)
PROTECTED_PATHS = [
    Path("/etc"),
    Path("/usr"),
    Path("/boot"),
    Path("/root"),
    Path("/sys"),
    Path("/proc"),
    WINDOWS_SYSTEM32,
    PROGRAM_FILES,
    Path("C:/Windows"),
]


def is_protected_path(path: Path) -> bool:
    """Check if a path is in a protected system location
    
    Args:
        path: Path to check
        
    Returns:
        True if path is protected
    """
    path = Path(path).resolve()
    
    for protected in PROTECTED_PATHS:
        try:
            if path.is_relative_to(protected):
                return True
        except (ValueError, AttributeError):
            # Python < 3.9 doesn't have is_relative_to
            try:
                path.relative_to(protected)
                return True
            except ValueError:
                pass
    
    return False


# Convenience exports
__all__ = [
    # Directories
    'HOME_DIR',
    'TEMP_DIR',
    'WINDOWS_SYSTEM32',
    'PROGRAM_FILES',
    'PROGRAM_FILES_X86',
    'X11_SOCKET',
    'RESOLV_CONF',
    'ETC_SUDOERS_DIR',
    'ETC_SSH_CONFIG',
    'USR_LOCAL_BINS',
    'BASHRC',
    'PROFILE',
    'CLAUDE_CONFIG_DIR',
    'CLAUDE_CONFIG_FILE',
    'CLAUDE_LOG_FILE',
    'CLAUDE_TEMP_DIR',
    'CLAUDE_STATE_FILE',
    'WSL_MOUNT_PREFIX',
    
    # Paths
    'VCXSRV_PATHS',
    'X11_LOCK_FILES',
    'SCREENSHOT_DEFAULT_PATH',
    'VCXSRV_INSTALLER_PATH',
    'PROTECTED_PATHS',
    
    # Functions
    'get_temp_dir',
    'get_vcxsrv_installer_path',
    'get_wsl_windows_path',
    'get_windows_path_from_wsl',
    'get_vcxsrv_search_paths',
    'ensure_dir',
    'get_secure_temp_file',
    'is_protected_path',
]