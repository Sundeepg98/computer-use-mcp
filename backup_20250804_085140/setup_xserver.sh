#!/bin/bash
# X Server Setup Script for Computer Use MCP

echo "Computer Use MCP - X Server Setup"
echo "================================="
echo

# Detect WSL
if grep -q Microsoft /proc/version; then
    echo "✓ WSL2 detected"
    WSL_MODE=true
    HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
    echo "  Windows host IP: $HOST_IP"
else
    echo "✗ Not running in WSL"
    WSL_MODE=false
fi

# Check current DISPLAY
echo
echo "Current Environment:"
echo "  DISPLAY: ${DISPLAY:-Not set}"

# Test X server connectivity
echo
echo "Testing X Server Connectivity:"
if timeout 3 xset q &>/dev/null; then
    echo "✓ X server is accessible at $DISPLAY"
    X_AVAILABLE=true
else
    echo "✗ No X server accessible"
    X_AVAILABLE=false
fi

# Check for required packages
echo
echo "Checking Required Packages:"
PACKAGES=("xorg" "xvfb" "x11-apps" "x11-utils" "xdotool" "scrot" "imagemagick")
MISSING_PACKAGES=()

for pkg in "${PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $pkg"; then
        echo "✓ $pkg installed"
    else
        echo "✗ $pkg not installed"
        MISSING_PACKAGES+=($pkg)
    fi
done

# Installation recommendations
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo
    echo "Missing packages detected. Install with:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y ${MISSING_PACKAGES[@]}"
fi

# WSL-specific recommendations
if [ "$WSL_MODE" = true ] && [ "$X_AVAILABLE" = false ]; then
    echo
    echo "WSL2 X Server Setup Instructions:"
    echo "================================="
    echo "1. Install X server on Windows (choose one):"
    echo "   - VcXsrv: https://sourceforge.net/projects/vcxsrv/"
    echo "   - X410: Available in Microsoft Store (paid)"
    echo "   - Xming: https://sourceforge.net/projects/xming/"
    echo
    echo "2. Configure X server on Windows:"
    echo "   - Launch with 'Multiple windows' mode"
    echo "   - Disable access control (allow connections)"
    echo "   - Enable 'Disable access control' in settings"
    echo
    echo "3. Set DISPLAY in WSL2:"
    echo "   export DISPLAY=$HOST_IP:0.0"
    echo
    echo "4. Add to ~/.bashrc for persistence:"
    echo "   echo 'export DISPLAY=\$(cat /etc/resolv.conf | grep nameserver | awk '\''{print \$2}'\''):0.0' >> ~/.bashrc"
fi

# Virtual display option
echo
echo "Alternative: Virtual Display (Xvfb)"
echo "==================================="
echo "For headless operation without a real display:"
echo "  Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &"
echo "  export DISPLAY=:99"
echo
echo "Or use the MCP tools:"
echo "  - start_xserver tool to start virtual display"
echo "  - xserver_status tool to check status"

# Test screenshot capability
echo
echo "Testing Screenshot Capability:"
if [ "$X_AVAILABLE" = true ]; then
    if scrot /tmp/test_screenshot.png 2>/dev/null; then
        echo "✓ Screenshot capture working"
        rm -f /tmp/test_screenshot.png
    else
        echo "✗ Screenshot capture failed"
    fi
else
    echo "✗ Cannot test - no X server available"
fi

echo
echo "Setup check complete!"