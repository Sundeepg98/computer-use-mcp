#!/usr/bin/env python3
"""
Validation script for computer-use-mcp package
Ensures all components are properly configured and working
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def validate_structure():
    """Validate directory structure"""
    required_dirs = ['src', 'tests', 'examples', 'bin', '.github/workflows']
    required_files = [
        'README.md', 'LICENSE', 'setup.py', 'requirements.txt',
        'package.json', 'Dockerfile', '.gitignore', 'CONTRIBUTING.md'
    ]
    
    print("📁 Validating directory structure...")
    
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"  ❌ Missing directory: {dir_name}")
            return False
        print(f"  ✅ Found: {dir_name}/")
    
    for file_name in required_files:
        if not Path(file_name).exists():
            print(f"  ❌ Missing file: {file_name}")
            return False
        print(f"  ✅ Found: {file_name}")
    
    return True

def validate_python_package():
    """Validate Python package configuration"""
    print("\n🐍 Validating Python package...")
    
    # Check setup.py
    if not Path('setup.py').exists():
        print("  ❌ setup.py not found")
        return False
    
    # Try to parse setup.py
    try:
        result = subprocess.run(
            [sys.executable, 'setup.py', '--name'],
            capture_output=True,
            text=True
        )
        package_name = result.stdout.strip()
        print(f"  ✅ Package name: {package_name}")
    except Exception as e:
        print(f"  ❌ Error reading setup.py: {e}")
        return False
    
    # Check requirements
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"  ✅ Dependencies: {len(deps)} packages")
    
    return True

def validate_npm_package():
    """Validate npm package configuration"""
    print("\n📦 Validating npm package...")
    
    if not Path('package.json').exists():
        print("  ❌ package.json not found")
        return False
    
    try:
        with open('package.json', 'r') as f:
            package = json.load(f)
        
        print(f"  ✅ Package: {package.get('name', 'unknown')}")
        print(f"  ✅ Version: {package.get('version', 'unknown')}")
        
        # Check MCP configuration
        if 'mcp' in package:
            print(f"  ✅ MCP version: {package['mcp'].get('version', 'unknown')}")
            print(f"  ✅ MCP tools: {len(package['mcp'].get('tools', []))} tools")
        else:
            print("  ⚠️  No MCP configuration found")
    except Exception as e:
        print(f"  ❌ Error reading package.json: {e}")
        return False
    
    return True

def validate_docker():
    """Validate Docker configuration"""
    print("\n🐳 Validating Docker configuration...")
    
    if not Path('Dockerfile').exists():
        print("  ❌ Dockerfile not found")
        return False
    
    with open('Dockerfile', 'r') as f:
        content = f.read()
        
    # Check for key components
    checks = [
        ('FROM python:', 'Base image'),
        ('WORKDIR', 'Working directory'),
        ('COPY', 'Copy instructions'),
        ('CMD', 'Default command'),
    ]
    
    for pattern, desc in checks:
        if pattern in content:
            print(f"  ✅ {desc} configured")
        else:
            print(f"  ⚠️  {desc} might be missing")
    
    return True

def validate_source_code():
    """Validate source code files"""
    print("\n💻 Validating source code...")
    
    required_modules = [
        'src/mcp_server.py',
        'src/computer_use_core.py',
        'src/safety_checks.py',
        'src/visual_analyzer.py',
    ]
    
    for module in required_modules:
        if Path(module).exists():
            print(f"  ✅ Found: {module}")
            # Try to import it
            try:
                module_name = module.replace('/', '.').replace('.py', '')
                # Basic syntax check
                with open(module, 'r') as f:
                    compile(f.read(), module, 'exec')
                print(f"     ✓ Syntax OK")
            except SyntaxError as e:
                print(f"     ❌ Syntax error: {e}")
                return False
        else:
            print(f"  ❌ Missing: {module}")
            return False
    
    return True

def validate_tests():
    """Validate test files"""
    print("\n🧪 Validating tests...")
    
    test_files = list(Path('tests').glob('test_*.py'))
    
    if not test_files:
        print("  ❌ No test files found")
        return False
    
    for test_file in test_files:
        print(f"  ✅ Found: {test_file}")
        # Check syntax
        try:
            with open(test_file, 'r') as f:
                compile(f.read(), str(test_file), 'exec')
            print(f"     ✓ Syntax OK")
        except SyntaxError as e:
            print(f"     ❌ Syntax error: {e}")
            return False
    
    return True

def validate_examples():
    """Validate example scripts"""
    print("\n📚 Validating examples...")
    
    example_files = list(Path('examples').glob('*.py'))
    
    if not example_files:
        print("  ⚠️  No example files found")
        return True  # Examples are optional
    
    for example_file in example_files:
        print(f"  ✅ Found: {example_file}")
    
    return True

def validate_ci():
    """Validate CI/CD configuration"""
    print("\n🚀 Validating CI/CD...")
    
    ci_file = Path('.github/workflows/ci.yml')
    
    if not ci_file.exists():
        print("  ⚠️  No CI workflow found")
        return True  # CI is optional
    
    print(f"  ✅ Found: {ci_file}")
    
    # Basic YAML validation
    try:
        import yaml
        with open(ci_file, 'r') as f:
            yaml.safe_load(f)
        print("     ✓ Valid YAML")
    except ImportError:
        print("     ⚠️  PyYAML not installed, skipping YAML validation")
    except Exception as e:
        print(f"     ❌ Invalid YAML: {e}")
        return False
    
    return True

def main():
    """Run all validations"""
    print("=" * 60)
    print("Computer Use MCP - Package Validation")
    print("=" * 60)
    
    # Change to package directory
    package_dir = Path(__file__).parent
    os.chdir(package_dir)
    
    validations = [
        ("Directory Structure", validate_structure),
        ("Python Package", validate_python_package),
        ("NPM Package", validate_npm_package),
        ("Docker Configuration", validate_docker),
        ("Source Code", validate_source_code),
        ("Tests", validate_tests),
        ("Examples", validate_examples),
        ("CI/CD", validate_ci),
    ]
    
    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} validation failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("-" * 60)
    print(f"Result: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 Package is ready to ship!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())