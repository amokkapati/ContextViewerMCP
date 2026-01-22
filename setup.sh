#!/bin/bash

# ContextViewer MCP Setup Script
# This script automates the installation process

set -e  # Exit on error

echo "=================================================="
echo "ContextViewer MCP - Setup Script"
echo "=================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Project directory: $SCRIPT_DIR"
echo ""

# Step 1: Check Python version
echo "[1/6] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Step 2: Create virtual environment
echo "[2/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Step 3: Activate virtual environment and install dependencies
echo "[3/6] Installing Python dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 4: Check for pdflatex (optional)
echo "[4/6] Checking for LaTeX (optional)..."
if command -v pdflatex &> /dev/null; then
    LATEX_VERSION=$(pdflatex --version | head -n1)
    echo "✓ Found: $LATEX_VERSION"
else
    echo "⚠ pdflatex not found. LaTeX rendering will not work."
    echo "  To install on macOS: brew install --cask mactex-no-gui"
    echo "  To install on Ubuntu: sudo apt-get install texlive-latex-base"
fi
echo ""

# Step 5: Run tests
echo "[5/6] Running tests..."
if python test_mcp.py; then
    echo "✓ Tests passed"
else
    echo "⚠ Some tests failed, but you can continue with setup"
fi
echo ""

# Step 6: Generate Claude Desktop configuration
echo "[6/6] Generating Claude Desktop configuration..."
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Generate the configuration
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
MCP_SERVER="$SCRIPT_DIR/mcp_server.py"

cat > claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "context-viewer": {
      "command": "$VENV_PYTHON",
      "args": [
        "$MCP_SERVER"
      ]
    }
  }
}
EOF

echo "✓ Configuration generated at: claude_desktop_config.json"
echo ""

# Check if Claude Desktop config exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "⚠ Claude Desktop configuration already exists at:"
    echo "  $CLAUDE_CONFIG_FILE"
    echo ""
    echo "To add ContextViewer MCP, merge the content from:"
    echo "  $SCRIPT_DIR/claude_desktop_config.json"
    echo ""
else
    echo "To complete setup, copy the configuration:"
    echo "  cp claude_desktop_config.json \"$CLAUDE_CONFIG_FILE\""
    echo ""
fi

# Summary
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add ContextViewer to Claude Desktop:"
echo "   - Edit: $CLAUDE_CONFIG_FILE"
echo "   - Add the content from: $SCRIPT_DIR/claude_desktop_config.json"
echo ""
echo "2. Restart Claude Desktop completely"
echo ""
echo "3. In Claude, try:"
echo "   'Can you open the context viewer?'"
echo ""
echo "For more information:"
echo "  - Installation guide: cat INSTALL.md"
echo "  - Quick start guide: cat QUICKSTART.md"
echo "  - Full documentation: cat README.md"
echo ""
echo "To run the web viewer standalone:"
echo "  source venv/bin/activate"
echo "  python server.py"
echo ""
echo "=================================================="
