#!/usr/bin/env python3
"""
Migration script to convert test_mode tests to proper dependency injection

This script analyzes test files and converts them from the anti-pattern:
    core = ComputerUseCore(test_mode=True)
    
To the proper pattern:
    mock_screenshot = Mock()
    core = ComputerUseCore(screenshot_handler=mock_screenshot)
    
Usage:
    python migrate_test_mode.py [--dry-run] [--file <specific_file>]
"""

import ast
import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class TestModeMigrator(ast.NodeTransformer):
    """AST transformer to migrate test_mode usage"""
    
    def __init__(self):
        self.imports_needed = set()
        self.setup_modifications = []
        self.test_mode_usages = []
    
    def visit_Call(self, node):
        """Visit function calls to find test_mode usage"""
        self.generic_visit(node)
        
        # Check for ComputerUseCore(test_mode=True)
        if (isinstance(node.func, ast.Name) and 
            node.func.id in ['ComputerUseCore', 'ComputerUseServer']):
            
            # Check for test_mode in keywords
            for keyword in node.keywords:
                if keyword.arg == 'test_mode':
                    self.test_mode_usages.append(node)
                    # Remove test_mode argument
                    node.keywords = [k for k in node.keywords if k.arg != 'test_mode']
                    # Mark that we need Mock import
                    self.imports_needed.add('Mock')
        
        return node
    
    def visit_Assign(self, node):
        """Visit assignments to track test_mode usage"""
        self.generic_visit(node)
        
        # Check for self.core = ComputerUseCore(test_mode=True)
        if (isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name) and
            node.value.func.id in ['ComputerUseCore', 'ComputerUseServer']):
            
            has_test_mode = any(k.arg == 'test_mode' for k in node.value.keywords)
            if has_test_mode:
                # Record that we need to modify this assignment
                target_name = None
                if isinstance(node.targets[0], ast.Attribute):
                    target_name = node.targets[0].attr
                elif isinstance(node.targets[0], ast.Name):
                    target_name = node.targets[0].id
                
                if target_name:
                    self.setup_modifications.append({
                        'var_name': target_name,
                        'class_name': node.value.func.id,
                        'node': node
                    })
        
        return node


def generate_mock_setup(class_name: str, var_name: str) -> List[str]:
    """Generate mock setup code for a given class"""
    lines = []
    
    if class_name == 'ComputerUseCore':
        lines.extend([
            f"# Create mocks for {var_name}",
            f"mock_screenshot_handler_{var_name} = Mock()",
            f"mock_screenshot_handler_{var_name}.capture.return_value = b'test_screenshot_data'",
            f"mock_input_handler_{var_name} = Mock()",
            f"mock_safety_checker_{var_name} = Mock()",
            f"mock_safety_checker_{var_name}.is_safe.return_value = True",
            f"mock_safety_checker_{var_name}.check_text_safety.return_value = True",
            "",
            f"# Create {var_name} with mocked dependencies",
            f"{var_name} = {class_name}(",
            f"    screenshot_handler=mock_screenshot_handler_{var_name},",
            f"    input_handler=mock_input_handler_{var_name},",
            f"    safety_checker=mock_safety_checker_{var_name}",
            f")",
        ])
    elif class_name == 'ComputerUseServer':
        lines.extend([
            f"# Create mocks for {var_name}",
            f"mock_computer_{var_name} = Mock()",
            f"mock_safety_{var_name} = Mock()",
            f"mock_safety_{var_name}.check_text_safety.return_value = True",
            "",
            f"# Create {var_name} and inject mocks",
            f"{var_name} = {class_name}()",
            f"if hasattr({var_name}, 'computer'):",
            f"    {var_name}.computer = mock_computer_{var_name}",
            f"if hasattr({var_name}, 'safety_checker'):",
            f"    {var_name}.safety_checker = mock_safety_{var_name}",
        ])
    
    return lines


def migrate_file(file_path: Path, dry_run: bool = False) -> Dict[str, any]:
    """Migrate a single test file"""
    result = {
        'file': str(file_path),
        'test_mode_found': False,
        'migrated': False,
        'error': None,
        'changes': []
    }
    
    try:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file has test_mode
        if 'test_mode=True' not in content and 'test_mode = True' not in content:
            return result
        
        result['test_mode_found'] = True
        
        # Parse AST
        tree = ast.parse(content)
        
        # Apply migrations
        migrator = TestModeMigrator()
        new_tree = migrator.visit(tree)
        
        if not migrator.test_mode_usages and not migrator.setup_modifications:
            return result
        
        # Generate new content
        lines = content.split('\n')
        
        # Add Mock import if needed
        if migrator.imports_needed:
            import_added = False
            for i, line in enumerate(lines):
                if 'from unittest.mock import' in line:
                    if 'Mock' not in line:
                        lines[i] = line.rstrip() + ', Mock'
                    import_added = True
                    break
                elif 'import unittest' in line:
                    lines.insert(i + 1, 'from unittest.mock import Mock, patch')
                    import_added = True
                    break
            
            if not import_added:
                # Add at the top after other imports
                for i, line in enumerate(lines):
                    if line.startswith('import') or line.startswith('from'):
                        continue
                    lines.insert(i, 'from unittest.mock import Mock, patch')
                    break
        
        # Generate mock setup code
        for mod in migrator.setup_modifications:
            # Find the line with the assignment
            for i, line in enumerate(lines):
                if f"{mod['var_name']} = {mod['class_name']}(test_mode=True)" in line:
                    # Replace with mock setup
                    indent = len(line) - len(line.lstrip())
                    mock_lines = generate_mock_setup(mod['class_name'], mod['var_name'])
                    
                    # Apply proper indentation
                    mock_lines = [' ' * indent + ml if ml else '' for ml in mock_lines]
                    
                    # Replace the line
                    lines[i:i+1] = mock_lines
                    result['changes'].append({
                        'line': i,
                        'old': line,
                        'new': '\n'.join(mock_lines)
                    })
                    break
        
        # Remove any remaining test_mode=True
        new_lines = []
        for line in lines:
            new_line = re.sub(r'test_mode\s*=\s*True,?\s*', '', line)
            new_line = re.sub(r',\s*test_mode\s*=\s*True', '', new_line)
            new_line = re.sub(r'\(\s*test_mode\s*=\s*True\s*\)', '()', new_line)
            new_lines.append(new_line)
        
        # Write back if not dry run
        new_content = '\n'.join(new_lines)
        
        if not dry_run:
            # Backup original
            backup_path = file_path.with_suffix('.py.bak')
            with open(backup_path, 'w') as f:
                f.write(content)
            
            # Write new content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            result['migrated'] = True
            result['backup'] = str(backup_path)
        else:
            result['preview'] = new_content
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def find_test_files(directory: Path) -> List[Path]:
    """Find all test files in directory"""
    return list(directory.glob('test_*.py'))


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate test_mode tests to proper mocking')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--file', type=str, help='Migrate specific file only')
    parser.add_argument('--directory', type=str, default='tests', help='Test directory (default: tests)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TEST MODE MIGRATION SCRIPT")
    print("=" * 70)
    print()
    
    # Find files to migrate
    if args.file:
        files = [Path(args.file)]
    else:
        test_dir = Path(args.directory)
        if not test_dir.exists():
            print(f"Error: Test directory '{test_dir}' not found")
            return 1
        files = find_test_files(test_dir)
    
    print(f"Found {len(files)} test files to analyze")
    print()
    
    # Migrate each file
    results = []
    for file in files:
        print(f"Analyzing {file}...")
        result = migrate_file(file, dry_run=args.dry_run)
        results.append(result)
        
        if result['test_mode_found']:
            print(f"  ✓ Found test_mode usage")
            if result['migrated']:
                print(f"  ✓ Migrated successfully (backup: {result['backup']})")
            elif args.dry_run:
                print(f"  → Would migrate (dry run)")
            elif result['error']:
                print(f"  ✗ Error: {result['error']}")
        else:
            print(f"  - No test_mode usage found")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_files = len(results)
    files_with_test_mode = sum(1 for r in results if r['test_mode_found'])
    files_migrated = sum(1 for r in results if r['migrated'])
    files_with_errors = sum(1 for r in results if r['error'])
    
    print(f"Total files analyzed: {total_files}")
    print(f"Files with test_mode: {files_with_test_mode}")
    print(f"Files migrated: {files_migrated}")
    print(f"Files with errors: {files_with_errors}")
    
    if args.dry_run:
        print()
        print("This was a dry run. No files were modified.")
        print("Run without --dry-run to apply changes.")
    
    # Show example of changes
    if args.dry_run and results:
        for result in results:
            if result.get('changes'):
                print()
                print(f"Example changes for {result['file']}:")
                for change in result['changes'][:2]:  # Show first 2 changes
                    print(f"  Line {change['line']}:")
                    print(f"    OLD: {change['old']}")
                    print(f"    NEW: {change['new'].split(chr(10))[0]}...")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())