# Computer-Use MCP Lite Packaging

## 📦 Package Information

- **Name**: computer-use-mcp-lite
- **Version**: 2.1.0
- **Format**: Python wheel (.whl) and source distribution (.tar.gz)
- **Build System**: setuptools with pyproject.toml

## ✅ Current Status

### Built Packages
```
dist/
├── computer_use_mcp_lite-2.1.0-py3-none-any.whl  (114K)
└── computer_use_mcp_lite-2.1.0.tar.gz            (105K)
```

### Auto-Packaging Enabled
- **Pre-commit hook**: Automatically builds package on every commit
- **Location**: `.git/hooks/pre-commit`
- **Behavior**: Builds and adds packages to commit automatically

## 🏭 Manual Building

### Prerequisites
```bash
# Create build environment (one-time)
uv venv build-env
source build-env/bin/activate
uv pip install build wheel
```

### Build Command
```bash
source build-env/bin/activate
python3 -m build --wheel --sdist
```

## 🚀 Installation Methods

### From Wheel
```bash
pip install dist/computer_use_mcp_lite-2.1.0-py3-none-any.whl
```

### From Source
```bash
pip install dist/computer_use_mcp_lite-2.1.0.tar.gz
```

### Development Mode
```bash
pip install -e .
```

## 🔄 Auto-Packaging Flow

1. **Make changes** to code
2. **Commit changes**: `git commit -m "message"`
3. **Hook triggers**: Pre-commit hook automatically:
   - Creates/activates build environment
   - Builds wheel and source distribution
   - Adds packages to commit
   - Shows success/failure message

## 📋 Package Contents

### Included Modules
- `mcp.lite_server` - Main MCP server
- `mcp.core` - Core functionality
- `mcp.input` - Input handling
- `mcp.screenshot` - Screenshot capture
- `mcp.platforms` - Platform detection
- `mcp.utils` - Utilities

### Entry Point
```python
computer-use-mcp = "mcp.mcp_server:main"
```

## 🛠️ Configuration

### pyproject.toml
- **Build system**: setuptools>=61.0
- **Python requirement**: >=3.8
- **Dependencies**: jsonschema, Pillow, numpy

### Version Management
- Version defined in `pyproject.toml`
- Update before major releases
- Follows semantic versioning (MAJOR.MINOR.PATCH)

## 📤 Publishing

### To PyPI (when ready)
```bash
# Install twine
pip install twine

# Upload to PyPI
twine upload dist/computer_use_mcp_lite-2.1.0-*
```

### To Private Registry
```bash
# Configure .pypirc with registry URL
twine upload -r private dist/computer_use_mcp_lite-2.1.0-*
```

## 📈 Version History

| Version | Date | Changes |
|---------|------|----------|
| 2.1.0 | 2025-01-10 | Lite version with auto-packaging |
| 1.0.0 | 2025-01-03 | Initial bloated version |

## ✅ Auto-Packaging Test

### Test Commit (2025-01-10)
- Added `__version__` to lite_server.py
- Testing auto-packaging hook functionality
- Verified packages are built and added automatically

## ✅ Verification

### Check Package Contents
```bash
# List wheel contents
unzip -l dist/computer_use_mcp_lite-2.1.0-py3-none-any.whl

# Extract and inspect
cd /tmp
whl2tar dist/computer_use_mcp_lite-2.1.0-py3-none-any.whl
```

### Test Installation
```bash
# Create test environment
uv venv test-install
source test-install/bin/activate

# Install package
pip install dist/computer_use_mcp_lite-2.1.0-py3-none-any.whl

# Test import
python3 -c "from mcp.lite_server import MCPServer; print('Success!')"
```

## 🎯 Benefits of Auto-Packaging

1. **Consistency**: Every commit has a corresponding package
2. **Traceability**: Package version matches git history
3. **Convenience**: No manual build steps needed
4. **CI/CD Ready**: Packages ready for deployment
5. **Distribution**: Easy to share and install

---

**Auto-packaging is ACTIVE** - Every commit automatically builds and includes the package!