#!/bin/bash
# Install git hooks for Robot Vacuum Cleaner project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🪝 Installing git hooks..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check if hooks directory exists
if [ ! -d "hooks" ]; then
    echo -e "${RED}❌ Error: hooks/ directory not found${NC}"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install hooks
for hook in hooks/*; do
    if [ -f "$hook" ]; then
        hook_name=$(basename "$hook")
        echo "Installing $hook_name..."

        # Copy hook to .git/hooks
        cp "$hook" ".git/hooks/$hook_name"

        # Make hook executable
        chmod +x ".git/hooks/$hook_name"

        echo -e "${GREEN}✓ Installed $hook_name${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ All hooks installed successfully!${NC}"
echo ""
echo "Installed hooks:"
ls -1 .git/hooks/ | grep -v ".sample$" | sed 's/^/  - /'

echo ""
echo "To skip a hook temporarily, use: git commit --no-verify"

exit 0
