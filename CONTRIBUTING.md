# Contributing to Computer Use MCP

Thank you for your interest in contributing to Computer Use MCP! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Provide clear reproduction steps
4. Include system information (OS, Python version, etc.)
5. Add relevant logs and screenshots

### Suggesting Features

1. Open a discussion first for major features
2. Explain the use case and benefits
3. Consider implementation complexity
4. Be open to alternative solutions

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our guidelines
4. Add or update tests as needed
5. Update documentation
6. Commit with descriptive messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 18+ (for npm package)
- Docker (optional)
- Git

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/computer-use-mcp.git
cd computer-use-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in editable mode

# Install dev dependencies
pip install pytest pytest-cov black pylint mypy
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_safety.py

# Run with verbose output
python -m pytest -v tests/
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with pylint
pylint src/

# Type checking with mypy
mypy src/

# Run all checks
make lint  # If Makefile is available
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 88)
- Add type hints where possible
- Write docstrings for all public functions/classes
- Keep functions focused and small

### Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or fixes
- `chore`: Maintenance tasks

Examples:
```
feat(tools): add double-click support to click tool
fix(safety): prevent command injection in type tool
docs(readme): update installation instructions
```

### Testing Guidelines

- Write tests for new features
- Maintain or improve code coverage
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies

Example test structure:
```python
def test_feature_normal_case():
    """Test feature works in normal conditions"""
    # Arrange
    # Act
    # Assert

def test_feature_edge_case():
    """Test feature handles edge cases"""
    # ...

def test_feature_error_handling():
    """Test feature handles errors gracefully"""
    # ...
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new code
- Update API documentation
- Include examples for new features
- Keep documentation in sync with code

## Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Update documentation
   - Add entry to CHANGELOG (if exists)
   - Rebase on latest main branch

2. **PR Description:**
   - Describe what changes you made
   - Explain why the changes are needed
   - List any breaking changes
   - Reference related issues

3. **Review Process:**
   - Address reviewer feedback promptly
   - Keep PR focused and manageable
   - Be patient - reviews take time
   - Squash commits if requested

## Release Process

Releases are managed by maintainers:

1. Version bump in package files
2. Update CHANGELOG
3. Create git tag
4. GitHub Actions handles publishing

## Getting Help

- Open a discussion for questions
- Join our community chat (if available)
- Check documentation first
- Be specific when asking for help

## Recognition

Contributors are recognized in:
- GitHub contributors page
- README.md acknowledgments
- Release notes

Thank you for contributing! 🎉