# Makefile for computer-use-mcp
# Automation for building, testing, and deploying

.PHONY: help install test lint format build clean docker publish dev all

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
PYLINT := $(PYTHON) -m pylint
MYPY := $(PYTHON) -m mypy
DOCKER := docker
NPM := npm

# Directories
SRC_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples
DIST_DIR := dist
BUILD_DIR := build
COVERAGE_DIR := htmlcov

# Default target
help:
	@echo "Computer Use MCP - Makefile Commands"
	@echo "===================================="
	@echo "make install    - Install package in development mode"
	@echo "make test       - Run all tests with coverage"
	@echo "make lint       - Run linting checks"
	@echo "make format     - Format code with Black"
	@echo "make build      - Build distribution packages"
	@echo "make docker     - Build Docker image"
	@echo "make clean      - Remove build artifacts"
	@echo "make publish    - Publish to PyPI and npm"
	@echo "make dev        - Install dev dependencies"
	@echo "make all        - Run format, lint, test, and build"

# Install package in development mode
install:
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

# Install development dependencies
dev:
	$(PIP) install -e .[dev]
	pre-commit install

# Run tests with coverage
test:
	@echo "Running tests with coverage..."
	$(PYTEST) $(TEST_DIR) \
		--cov=$(SRC_DIR) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		-v

# Run specific test file
test-file:
	@echo "Running test file: $(FILE)"
	$(PYTEST) $(FILE) -v

# Run TDD tests
test-tdd:
	@echo "Running TDD tests..."
	$(PYTHON) -m unittest tests.test_package_tdd -v

# Lint code
lint:
	@echo "Running pylint..."
	$(PYLINT) $(SRC_DIR) || true
	@echo "Running mypy..."
	$(MYPY) $(SRC_DIR) || true

# Format code with Black
format:
	@echo "Formatting code with Black..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)

# Check formatting without modifying
format-check:
	@echo "Checking code formatting..."
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	$(PYTHON) -m build
	@echo "Checking distribution..."
	twine check $(DIST_DIR)/*

# Build Docker image
docker:
	@echo "Building Docker image..."
	$(DOCKER) build -t computer-use-mcp:latest .
	@echo "Image built successfully"

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	$(DOCKER) run -it --rm \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		computer-use-mcp:latest

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR) *.egg-info
	rm -rf $(COVERAGE_DIR) .coverage* coverage.xml
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

# Publish to PyPI
publish-pypi: build
	@echo "Publishing to PyPI..."
	twine upload $(DIST_DIR)/*

# Publish to npm
publish-npm:
	@echo "Publishing to npm..."
	$(NPM) publish --access public

# Publish to all platforms
publish: publish-pypi publish-npm
	@echo "Published to PyPI and npm"

# Run security checks
security:
	@echo "Running security checks..."
	bandit -r $(SRC_DIR) -f json -o bandit-report.json || true
	safety check --json || true

# Generate documentation
docs:
	@echo "Generating documentation..."
	sphinx-build -b html docs docs/_build

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
	pre-commit install

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	$(PIP) list --outdated
	$(PIP) install --upgrade pip setuptools wheel

# Run examples
run-examples:
	@echo "Running examples..."
	$(PYTHON) $(EXAMPLES_DIR)/basic_usage.py
	$(PYTHON) $(EXAMPLES_DIR)/advanced_automation.py

# Validate package
validate:
	@echo "Validating package..."
	$(PYTHON) validate_package.py

# Run all checks (format, lint, test, build)
all: format lint test build
	@echo "All checks completed successfully!"

# Development server
dev-server:
	$(PYTHON) $(SRC_DIR)/mcp_server.py

# Create release
release:
	@echo "Creating release..."
	@read -p "Enter version number: " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version

.DEFAULT_GOAL := help