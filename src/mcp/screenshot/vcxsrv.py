#!/usr/bin/env python3
"""
VcXsrv X11 screenshot implementation for Windows
Enables X11 application screenshots via VcXsrv server
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any, List
from .base import ScreenshotBase, ScreenshotCaptureError

logger = logging.getLogger(__name__)


class VcXsrvScreenshot(ScreenshotBase):
    """Screenshot implementation using VcXsrv X11 server on Windows"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize VcXsrv screenshot handler"""
        super().__init__(config)
        self.vcxsrv_info = self._detect_vcxsrv()
        self.display = self._get_display()
        self.screenshot_tools = self._detect_screenshot_tools()
        
    def _detect_vcxsrv(self) -> Dict[str, Any]:
        """Detect VcXsrv installation and status"""
        try:
            from ..vcxsrv_detector import VcXsrvDetector
            detector = VcXsrvDetector()
            return detector.detect_vcxsrv()
        except Exception as e:
            logger.error(f"Failed to detect VcXsrv: {e}")
            return {'installed': False, 'running': False}
    
    def _get_display(self) -> Optional[str]:
        """Get the best available X11 display"""
        if not self.vcxsrv_info.get('xdisplay_available'):
            return None
        
        # Use recommended display from detector
        recommended = self.vcxsrv_info.get('recommended_display')
        if recommended:
            return recommended
        
        # Fallback to first available display
        display_numbers = self.vcxsrv_info.get('display_numbers', [])
        if display_numbers:
            return f":{display_numbers[0]}"
        
        return None
    
    def _detect_screenshot_tools(self) -> Dict[str, bool]:
        """Detect available X11 screenshot tools"""
        tools = {
            'import': False,    # ImageMagick
            'scrot': False,     # SCReenshOT
            'xwd': False,       # X Window Dump
            'gnome-screenshot': False
        }
        
        if not self.display:
            return tools
        
        # Set environment for X11
        env = os.environ.copy()
        env['DISPLAY'] = self.display
        
        for tool in tools.keys():
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    timeout=3,
                    env=env
                )
                tools[tool] = result.returncode == 0
            except Exception:
                continue
        
        logger.info(f"Available screenshot tools: {[k for k, v in tools.items() if v]}")
        return tools
    
    def is_available(self) -> bool:
        """Check if VcXsrv screenshot is available"""
        return (
            self.vcxsrv_info.get('installed', False) and
            self.vcxsrv_info.get('running', False) and
            self.display is not None and
            any(self.screenshot_tools.values())
        )
    
    def capture(self, **kwargs) -> bytes:
        """Capture screenshot using X11 tools via VcXsrv"""
        if not self.is_available():
            raise ScreenshotCaptureError(
                f"VcXsrv screenshot not available. "
                f"VcXsrv installed: {self.vcxsrv_info.get('installed')}, "
                f"running: {self.vcxsrv_info.get('running')}, "
                f"display: {self.display}, "
                f"tools: {self.screenshot_tools}"
            )
        
        logger.info(f"Capturing screenshot via VcXsrv display {self.display}")
        
        # Try screenshot tools in order of preference
        methods = [
            ('import', self._capture_with_imagemagick),
            ('scrot', self._capture_with_scrot),
            ('xwd', self._capture_with_xwd),
            ('gnome-screenshot', self._capture_with_gnome)
        ]
        
        for tool, method in methods:
            if self.screenshot_tools.get(tool, False):
                try:
                    return method(**kwargs)
                except Exception as e:
                    logger.warning(f"Screenshot with {tool} failed: {e}")
                    continue
        
        raise ScreenshotCaptureError(
            "All VcXsrv screenshot methods failed. "
            "Ensure X11 screenshot tools are installed."
        )
    
    def _capture_with_imagemagick(self, **kwargs) -> bytes:
        """Capture using ImageMagick import command"""
        region = kwargs.get('region')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Build import command
            cmd = ['import']
            
            if region:
                # Specific region: import -window root -crop WxH+X+Y
                cmd.extend([
                    '-window', 'root',
                    '-crop', f"{region['width']}x{region['height']}+{region['x']}+{region['y']}"
                ])
            else:
                # Full screen: import -window root
                cmd.extend(['-window', 'root'])
            
            cmd.append(tmp_path)
            
            # Set X11 environment
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            # Execute import command
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                raise Exception(f"import command failed: {result.stderr.decode()}")
            
            # Read the image data
            with open(tmp_path, 'rb') as f:
                return f.read()
                
        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _capture_with_scrot(self, **kwargs) -> bytes:
        """Capture using scrot command"""
        region = kwargs.get('region')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            cmd = ['scrot']
            
            if region:
                # Specific region: scrot -a x,y,w,h
                cmd.extend([
                    '-a', f"{region['x']},{region['y']},{region['width']},{region['height']}"
                ])
            
            cmd.append(tmp_path)
            
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                raise Exception(f"scrot command failed: {result.stderr.decode()}")
            
            with open(tmp_path, 'rb') as f:
                return f.read()
                
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _capture_with_xwd(self, **kwargs) -> bytes:
        """Capture using xwd command"""
        # xwd produces XWD format, need to convert to PNG
        
        with tempfile.NamedTemporaryFile(suffix='.xwd', delete=False) as xwd_tmp:
            xwd_path = xwd_tmp.name
            
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as png_tmp:
            png_path = png_tmp.name
        
        try:
            # Capture with xwd
            cmd = ['xwd', '-root', '-out', xwd_path]
            
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                raise Exception(f"xwd command failed: {result.stderr.decode()}")
            
            # Convert XWD to PNG using ImageMagick convert
            convert_cmd = ['convert', xwd_path, png_path]
            convert_result = subprocess.run(
                convert_cmd,
                capture_output=True,
                timeout=10
            )
            
            if convert_result.returncode != 0:
                raise Exception(f"XWD to PNG conversion failed: {convert_result.stderr.decode()}")
            
            with open(png_path, 'rb') as f:
                return f.read()
                
        finally:
            for path in [xwd_path, png_path]:
                try:
                    os.unlink(path)
                except:
                    pass
    
    def _capture_with_gnome(self, **kwargs) -> bytes:
        """Capture using gnome-screenshot"""
        region = kwargs.get('region')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            cmd = ['gnome-screenshot', '--file', tmp_path]
            
            if region:
                # Area selection
                cmd.append('--area')
            else:
                # Full screen
                cmd.append('--window')
            
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                env=env
            )
            
            if result.returncode != 0:
                raise Exception(f"gnome-screenshot failed: {result.stderr.decode()}")
            
            with open(tmp_path, 'rb') as f:
                return f.read()
                
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get monitor information via X11"""
        if not self.is_available():
            return []
        
        monitors = []
        
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            # Try xrandr for monitor info
            result = subprocess.run(
                ['xrandr', '--query'],
                capture_output=True,
                text=True,
                timeout=5,
                env=env
            )
            
            if result.returncode == 0:
                # Parse xrandr output
                current_monitor = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if ' connected ' in line:
                        # Monitor line: "DisplayPort-0 connected 1920x1080+0+0 ..."
                        parts = line.split()
                        name = parts[0]
                        
                        if len(parts) >= 3:
                            resolution_part = parts[2]
                            if 'x' in resolution_part and '+' in resolution_part:
                                # Parse "1920x1080+0+0"
                                res_pos = resolution_part.split('+')
                                if len(res_pos) >= 3:
                                    width_height = res_pos[0]
                                    x_offset = int(res_pos[1])
                                    y_offset = int(res_pos[2])
                                    
                                    if 'x' in width_height:
                                        width, height = map(int, width_height.split('x'))
                                        
                                        monitors.append({
                                            'name': name,
                                            'width': width,
                                            'height': height,
                                            'x': x_offset,
                                            'y': y_offset,
                                            'primary': 'primary' in line
                                        })
            
        except Exception as e:
            logger.debug(f"Failed to get monitor info via xrandr: {e}")
            
            # Fallback: single monitor assumption
            monitors = [{
                'name': 'default',
                'width': 1920,
                'height': 1080,
                'x': 0,
                'y': 0,
                'primary': True
            }]
        
        return monitors
    
    def get_vcxsrv_status(self) -> Dict[str, Any]:
        """Get detailed VcXsrv status"""
        return {
            'vcxsrv_info': self.vcxsrv_info,
            'display': self.display,
            'screenshot_tools': self.screenshot_tools,
            'available': self.is_available()
        }
    
    def start_vcxsrv_if_needed(self) -> Dict[str, Any]:
        """Start VcXsrv if not running"""
        if self.vcxsrv_info.get('running'):
            return {
                'success': True,
                'message': 'VcXsrv already running',
                'display': self.display
            }
        
        if not self.vcxsrv_info.get('installed'):
            return {
                'success': False,
                'error': 'VcXsrv not installed',
                'suggestion': 'Install VcXsrv from https://sourceforge.net/projects/vcxsrv/'
            }
        
        try:
            from ..vcxsrv_detector import VcXsrvDetector
            detector = VcXsrvDetector()
            result = detector.start_vcxsrv(display=0)
            
            if result['success']:
                # Refresh our state
                self._cache = None
                self.vcxsrv_info = self._detect_vcxsrv()
                self.display = self._get_display()
                self.screenshot_tools = self._detect_screenshot_tools()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to start VcXsrv: {e}'
            }