# 🔧 Computer Use MCP - Refactoring Guide

## Overview

This guide explains the major refactoring of the Computer Use MCP codebase to eliminate the `test_mode` anti-pattern and implement proper dependency injection.

## 🚨 The Problem with test_mode

The original implementation used a `test_mode` flag that caused several critical issues:

```python
# ❌ BAD: test_mode anti-pattern
def __init__(self, test_mode=False):
    self.test_mode = test_mode
    
def screenshot(self):
    if self.test_mode:
        return {'data': b'mock_data'}  # Tests never exercise real code!
    # ... real implementation
```

### Why This Is Dangerous

1. **Zero Real Code Coverage**: Tests validate mock data, not actual functionality
2. **Production Code Pollution**: Business logic mixed with test logic
3. **False Confidence**: 100% passing tests don't mean working code
4. **Platform Bugs Hidden**: Platform-specific code never tested

## ✅ The Solution: Dependency Injection

The refactored architecture uses clean abstractions and dependency injection:

```python
# ✅ GOOD: Clean architecture with DI
class ComputerUseRefactored:
    def __init__(
        self,
        screenshot_provider: ScreenshotProvider,
        input_provider: InputProvider,
        platform_info: PlatformInfo,
        safety_validator: SafetyValidator,
        display_manager: DisplayManager
    ):
        # All dependencies injected - no test_mode needed!
```

## 📝 Migration Guide

### Step 1: Update Your Imports

```python
# Old
from computer_use_mcp.computer_use_core import ComputerUseCore

# New
from computer_use_mcp.factory_refactored import create_computer_use, create_computer_use_for_testing
```

### Step 2: Production Code

```python
# Old
core = ComputerUseCore(test_mode=False)

# New
core = create_computer_use()  # Automatically configured for platform
```

### Step 3: Test Code

```python
# Old - BAD
def test_screenshot():
    core = ComputerUseCore(test_mode=True)
    result = core.screenshot()  # Returns mock data!
    assert result['data'] == b'mock_screenshot_data'

# New - GOOD
def test_screenshot():
    mock_screenshot = Mock()
    mock_screenshot.capture.return_value = np.zeros((100, 100, 3))
    
    core = create_computer_use_for_testing(
        screenshot_provider=mock_screenshot
    )
    
    result = core.take_screenshot()
    mock_screenshot.capture.assert_called_once()  # Real behavior tested!
```

## 🏗️ Architecture Components

### 1. Abstractions (Protocols)

Located in `abstractions/__init__.py`:
- `ScreenshotProvider`: Interface for screenshot implementations
- `InputProvider`: Interface for input operations
- `PlatformInfo`: Interface for platform information
- `SafetyValidator`: Interface for safety checks
- `DisplayManager`: Interface for display management

### 2. Implementations

Located in `implementations/`:
- Platform-specific implementations of each protocol
- Can be swapped out for testing or different platforms

### 3. Factory Pattern

Located in `factory_refactored.py`:
- `create_computer_use()`: Creates production instance
- `create_computer_use_for_testing()`: Creates test instance with mocks

## 🔄 Converting Existing Tests

### Example: Screenshot Test

**Before (with test_mode):**
```python
class TestScreenshot(unittest.TestCase):
    def test_screenshot_in_test_mode(self):
        core = ComputerUseCore(test_mode=True)
        result = core.screenshot()
        
        # This doesn't test any real code!
        self.assertEqual(result['data'], b'mock_screenshot_data')
        self.assertTrue(result['test_mode'])
```

**After (with proper mocking):**
```python
class TestScreenshot(unittest.TestCase):
    def test_screenshot_capture_called(self):
        # Create mock screenshot provider
        mock_screenshot = Mock()
        mock_screenshot.capture.return_value = np.zeros((1920, 1080, 3))
        
        # Create instance with mock
        core = create_computer_use_for_testing(
            screenshot_provider=mock_screenshot
        )
        
        # Test the behavior
        result = core.take_screenshot()
        
        # Verify real interactions
        self.assertTrue(result['success'])
        mock_screenshot.capture.assert_called_once()
        self.assertEqual(result['data'].shape, (1920, 1080, 3))
```

### Example: Safety Testing

**Before:**
```python
def test_safety_check(self):
    core = ComputerUseCore(test_mode=True)
    # Safety checks bypassed in test mode!
    result = core.type_text("rm -rf /")
    self.assertTrue(result['success'])  # Dangerous!
```

**After:**
```python
def test_safety_check_blocks_dangerous_text(self):
    # Create mock safety validator
    mock_safety = Mock()
    mock_safety.validate_text.return_value = (False, "Dangerous command")
    
    core = create_computer_use_for_testing(
        safety_validator=mock_safety
    )
    
    result = core.type_text("rm -rf /")
    
    # Verify safety was checked
    mock_safety.validate_text.assert_called_with("rm -rf /")
    self.assertFalse(result['success'])
    self.assertIn("Safety check failed", result['error'])
```

## 🎯 Benefits of Refactoring

1. **Real Testing**: Tests exercise actual code paths
2. **Clean Architecture**: Separation of concerns, SOLID principles
3. **Platform Flexibility**: Easy to add new platform support
4. **Better Performance**: No test_mode checks in production
5. **Maintainability**: Clear interfaces and responsibilities

## 🔍 Finding test_mode Usage

To find all files using test_mode:

```bash
# Find test_mode in source
grep -r "test_mode" src/

# Find tests that need updating
grep -r "ComputerUseCore(test_mode=True)" tests/
```

## 📋 Refactoring Checklist

- [ ] Replace `ComputerUseCore` with `ComputerUseRefactored`
- [ ] Remove all `test_mode` parameters
- [ ] Convert tests to use proper mocks
- [ ] Update imports to use new factory functions
- [ ] Verify tests actually test real behavior
- [ ] Remove test-specific code from production classes
- [ ] Update documentation

## 🚀 Next Steps

1. **Phase 1**: Migrate core functionality (this guide)
2. **Phase 2**: Decompose large modules (mcp_server.py)
3. **Phase 3**: Implement async operations
4. **Phase 4**: Add comprehensive integration tests
5. **Phase 5**: Performance optimization

## ⚠️ Breaking Changes

The refactoring introduces breaking changes:

1. `ComputerUseCore(test_mode=True)` no longer exists
2. Method names changed: `screenshot()` → `take_screenshot()`
3. Return formats standardized with `success` field
4. All dependencies must be injected or use factory

## 📚 Additional Resources

- See `test_refactored_example.py` for complete test examples
- Review `abstractions/__init__.py` for interface definitions
- Check `factory_refactored.py` for instance creation patterns

---

Remember: **Real tests test real code**. The test_mode pattern created an illusion of quality while hiding real bugs. This refactoring ensures your tests provide actual confidence in your code's behavior.