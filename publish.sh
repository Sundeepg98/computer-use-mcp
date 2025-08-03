#!/bin/bash
# Computer Use MCP Publishing Script

set -e

echo "🚀 Computer Use MCP Publishing Assistant"
echo "========================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Are you in the computer-use-mcp directory?${NC}"
    exit 1
fi

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 found${NC}"
fi

if ! command_exists npm; then
    echo -e "${RED}✗ npm not found${NC}"
    echo "  Install Node.js from https://nodejs.org/"
else
    echo -e "${GREEN}✓ npm found${NC}"
fi

if ! command_exists docker; then
    echo -e "${YELLOW}⚠ Docker not found (optional)${NC}"
else
    echo -e "${GREEN}✓ Docker found${NC}"
fi

# Check Python packages
if ! python3 -c "import build" 2>/dev/null; then
    echo -e "${YELLOW}Installing build...${NC}"
    pip install --upgrade build
fi

if ! python3 -c "import twine" 2>/dev/null; then
    echo -e "${YELLOW}Installing twine...${NC}"
    pip install --upgrade twine
fi

# Menu
echo -e "\n${YELLOW}What would you like to do?${NC}"
echo "1. Build Python package"
echo "2. Check package with twine"
echo "3. Publish to Test PyPI"
echo "4. Publish to PyPI"
echo "5. Publish to npm"
echo "6. Create GitHub release"
echo "7. Build Docker image"
echo "8. Run all tests"
echo "9. Clean build artifacts"
echo "0. Exit"

read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Building Python package...${NC}"
        rm -rf dist/ build/ *.egg-info
        python3 -m build
        echo -e "${GREEN}✓ Package built successfully${NC}"
        ls -la dist/
        ;;
    
    2)
        echo -e "\n${YELLOW}Checking package...${NC}"
        twine check dist/*
        ;;
    
    3)
        echo -e "\n${YELLOW}Publishing to Test PyPI...${NC}"
        echo "Make sure you have configured ~/.pypirc with your Test PyPI token"
        read -p "Continue? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            twine upload --repository testpypi dist/*
            echo -e "${GREEN}✓ Published to Test PyPI${NC}"
            echo "Test installation: pip install --index-url https://test.pypi.org/simple/ computer-use-mcp"
        fi
        ;;
    
    4)
        echo -e "\n${YELLOW}Publishing to PyPI...${NC}"
        echo -e "${RED}⚠️  This will publish to the LIVE PyPI repository!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            twine upload dist/*
            echo -e "${GREEN}✓ Published to PyPI${NC}"
            echo "Install with: pip install computer-use-mcp"
        fi
        ;;
    
    5)
        echo -e "\n${YELLOW}Publishing to npm...${NC}"
        echo "Make sure you're logged in to npm (npm login)"
        read -p "Continue? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            npm publish
            echo -e "${GREEN}✓ Published to npm${NC}"
            echo "Use with: npx computer-use-mcp"
        fi
        ;;
    
    6)
        echo -e "\n${YELLOW}Creating GitHub release...${NC}"
        # Get current version
        VERSION=$(python3 setup.py --version)
        echo "Current version: $VERSION"
        echo ""
        echo "Steps to create release:"
        echo "1. Commit all changes: git add . && git commit -m 'Release v$VERSION'"
        echo "2. Create tag: git tag -a v$VERSION -m 'Release version $VERSION'"
        echo "3. Push changes: git push origin main"
        echo "4. Push tag: git push origin v$VERSION"
        echo "5. Go to: https://github.com/YOUR-USERNAME/computer-use-mcp/releases/new"
        echo "6. Select tag v$VERSION and create release"
        ;;
    
    7)
        echo -e "\n${YELLOW}Building Docker image...${NC}"
        docker build -t computer-use-mcp .
        echo -e "${GREEN}✓ Docker image built${NC}"
        echo "Tag and push:"
        echo "  docker tag computer-use-mcp:latest YOUR-USERNAME/computer-use-mcp:latest"
        echo "  docker push YOUR-USERNAME/computer-use-mcp:latest"
        ;;
    
    8)
        echo -e "\n${YELLOW}Running tests...${NC}"
        python3 -m pytest tests/ -v
        ;;
    
    9)
        echo -e "\n${YELLOW}Cleaning build artifacts...${NC}"
        rm -rf dist/ build/ *.egg-info __pycache__ .pytest_cache .coverage htmlcov/
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}✓ Cleaned${NC}"
        ;;
    
    0)
        echo "Goodbye!"
        exit 0
        ;;
    
    *)
        echo -e "${RED}Invalid choice${NC}"
        ;;
esac

echo -e "\n${YELLOW}Done! Run the script again for more options.${NC}"