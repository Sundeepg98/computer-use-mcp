#!/bin/bash
# Auto-increment version for each commit

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version' pyproject.toml | cut -d'"' -f2)

# Split version into parts
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Increment patch version
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

# Update pyproject.toml
sed -i "s/version = \"${CURRENT_VERSION}\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# Update __version__ in Python files
find src -name "*.py" -exec sed -i "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" {} \;

echo "✅ Version bumped: ${CURRENT_VERSION} → ${NEW_VERSION}"

# Option 2: Use commit hash for dev versions
# COMMIT_HASH=$(git rev-parse --short HEAD)
# DEV_VERSION="${MAJOR}.${MINOR}.${PATCH}.dev${COMMIT_HASH}"
# echo "Dev version: ${DEV_VERSION}"