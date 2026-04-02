#!/usr/bin/env sh
# ContextViewerMCP installer
# Usage: curl -fsSL https://raw.githubusercontent.com/amokkapati/ContextViewerMCP/main/scripts/install.sh | sh

set -e

INSTALL_DIR="$HOME/.cache/contextviewermcp"
REPO_DIR="$INSTALL_DIR/repo"
BIN_DIR="$INSTALL_DIR/bin"
REPO_URL="https://github.com/amokkapati/ContextViewerMCP.git"

echo "Installing ContextViewerMCP..."
echo ""

# --- 1. Clone or update repo ---
if [ -d "$REPO_DIR/.git" ]; then
    echo "Updating existing installation..."
    git -C "$REPO_DIR" pull --quiet
else
    echo "Cloning repository..."
    mkdir -p "$INSTALL_DIR"
    git clone --quiet "$REPO_URL" "$REPO_DIR"
fi
echo "✓ Repository ready"

# --- 2. Create virtual environment and install deps ---
if [ ! -f "$REPO_DIR/venv/bin/python" ]; then
    echo "Creating Python virtual environment..."
    if command -v uv > /dev/null 2>&1; then
        uv venv "$REPO_DIR/venv" --quiet
        uv pip install -q --python "$REPO_DIR/venv/bin/python" -r "$REPO_DIR/requirements.txt"
    else
        python3 -m venv "$REPO_DIR/venv"
        "$REPO_DIR/venv/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
    fi
    echo "✓ Dependencies installed"
else
    echo "✓ Virtual environment already exists"
fi

# --- 3. Install tectonic for LaTeX compilation ---
if command -v tectonic > /dev/null 2>&1; then
    echo "✓ tectonic already available"
elif command -v brew > /dev/null 2>&1; then
    echo "Installing tectonic for LaTeX compilation..."
    brew install tectonic
    echo "✓ tectonic installed"
else
    echo "⚠ Homebrew not found — skipping tectonic install."
    echo "  To enable LaTeX compilation, install Homebrew then run:"
    echo "    brew install tectonic"
fi

# --- 4. Make CLI executable ---
chmod +x "$REPO_DIR/contextviewermcp"

# --- 5. Create bin wrapper ---
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/contextviewermcp" <<WRAPPER
#!/usr/bin/env sh
exec "$REPO_DIR/contextviewermcp" "\$@"
WRAPPER
chmod +x "$BIN_DIR/contextviewermcp"
echo "✓ Installed to $BIN_DIR/contextviewermcp"

# --- 6. Print PATH instructions ---
echo ""
echo "============================================"
echo "  Installation complete!"
echo "============================================"
echo ""
echo "Add contextviewermcp to your PATH:"
echo ""

# Detect shell config file
if [ -n "$ZSH_VERSION" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi

echo "  echo 'export PATH=\"\$HOME/.cache/contextviewermcp/bin:\$PATH\"' >> $RC_FILE"
echo "  source $RC_FILE"
echo ""
echo "Then in any project directory:"
echo ""
echo "  contextviewermcp --setup claudecode   # set up Claude Code MCP integration"
echo "  contextviewermcp start                # open the viewer in your browser"
echo ""
