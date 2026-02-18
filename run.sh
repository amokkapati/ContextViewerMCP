#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=${PORT:-8765}
STATE_FILE="$HOME/.context-viewer-state.json"

usage() {
    echo "Usage: ./run.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start [port]    Start the ContextViewer server (default port: 8765)"
    echo "  stop [port]     Stop the running server"
    echo "  status [port]   Show server status and current selection"
    echo "  selection       Print the current text selection"
    echo "  setup           Install dependencies and generate Claude Desktop config"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start"
    echo "  ./run.sh start 3000"
    echo "  ./run.sh stop"
    echo "  ./run.sh selection"
    echo "  ./run.sh setup"
}

cmd_start() {
    local port=${1:-8765}
    cd "$SCRIPT_DIR"

    if lsof -i :$port > /dev/null 2>&1; then
        echo "✓ Server already running at http://localhost:$port"
        _show_state $port
        exit 0
    fi

    echo "Starting ContextViewer on port $port..."
    python3 server.py $port > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 1

    if lsof -i :$port > /dev/null 2>&1; then
        echo "✓ Server started at http://localhost:$port (PID: $SERVER_PID)"
        _show_state $port
        echo "To stop: ./run.sh stop $port"
    else
        echo "✗ Failed to start server"
        exit 1
    fi
}

cmd_stop() {
    local port=${1:-8765}

    if lsof -i :$port > /dev/null 2>&1; then
        PID=$(lsof -ti :$port)
        kill $PID
        echo "✓ Stopped server on port $port (PID: $PID)"
    else
        echo "No server running on port $port"
    fi

    TMP_FILE="$STATE_FILE.tmp"
    if [ -f "$TMP_FILE" ]; then
        rm "$TMP_FILE"
        echo "✓ Cleaned up temporary state file"
    fi

    echo "{}" > "$STATE_FILE"
    echo "✓ Reset context viewer state"
}

cmd_status() {
    local port=${1:-8765}

    if lsof -i :$port > /dev/null 2>&1; then
        echo "✓ Server running at http://localhost:$port"
    else
        echo "✗ No server running on port $port"
    fi

    _show_state $port
}

cmd_selection() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "No selection available. Open the viewer and select some text."
        exit 1
    fi

    if command -v jq &> /dev/null; then
        jq -r '.selection | if . then "File: \(.file_path)\nLines: \(.start_line)-\(.end_line)\n\n\(.selected_text)" else "No selection available" end' "$STATE_FILE"
    else
        python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
    sel = state.get('selection')
    if sel:
        print(f\"File: {sel['file_path']}\")
        print(f\"Lines: {sel['start_line']}-{sel['end_line']}\n\")
        print(sel['selected_text'])
    else:
        print('No selection available')
"
    fi
}

cmd_setup() {
    cd "$SCRIPT_DIR"
    echo "=================================================="
    echo "ContextViewer MCP - Setup"
    echo "=================================================="
    echo ""

    echo "[1/5] Checking Python..."
    if ! command -v python3 &> /dev/null; then
        echo "✗ Python 3 not found. Install it from https://python.org"
        exit 1
    fi
    echo "✓ Found $(python3 --version)"
    echo ""

    echo "[2/5] Checking uv..."
    if ! command -v uv &> /dev/null; then
        echo "✗ uv not installed. Install it with:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "✓ Found uv"
    echo ""

    echo "[3/5] Creating virtual environment..."
    if [ -d "venv" ]; then
        echo "⚠ Virtual environment already exists. Skipping..."
    else
        uv venv venv
        echo "✓ Virtual environment created"
    fi
    echo ""

    echo "[4/5] Installing dependencies..."
    source venv/bin/activate
    uv pip install -q -r requirements.txt
    echo "✓ Dependencies installed"
    echo ""

    echo "[5/5] Checking for LaTeX (optional)..."
    if command -v pdflatex &> /dev/null; then
        echo "✓ Found pdflatex"
    else
        echo "⚠ pdflatex not found. LaTeX rendering will not work."
        echo "  macOS: brew install --cask mactex-no-gui"
        echo "  Linux: sudo apt-get install texlive-latex-base"
    fi
    echo ""

    VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
    MCP_SERVER="$SCRIPT_DIR/mcp_server.py"
    cat > claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "context-viewer": {
      "command": "$VENV_PYTHON",
      "args": ["$MCP_SERVER"]
    }
  }
}
EOF

    CLAUDE_CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    echo "✓ Generated claude_desktop_config.json"
    echo ""

    if [ -f "$CLAUDE_CONFIG_FILE" ]; then
        echo "⚠ Claude Desktop config already exists. Merge manually:"
        echo "  $CLAUDE_CONFIG_FILE"
    else
        echo "To complete setup:"
        echo "  cp claude_desktop_config.json \"$CLAUDE_CONFIG_FILE\""
    fi

    echo ""
    echo "=================================================="
    echo "Setup complete. Run './run.sh start' to launch."
    echo "=================================================="
}

_show_state() {
    local port=${1:-8765}
    echo ""
    echo "💡 Claude: Read mcp_server.py for available MCP tools"
    echo "💡 Claude: Check ~/.context-viewer-state.json for selections"
    echo ""
    echo "📍 Navigation: update ~/.context-viewer-state.json with:"
    echo "   {\"server_url\": \"http://localhost:$port\", \"navigation\": {"
    echo "     \"command\": \"goto_line\", \"file_path\": \"file.py\","
    echo "     \"target\": LINE_NUMBER, \"timestamp\": UNIX_TIME, \"executed\": false"
    echo "   }}"
    echo "   Commands: goto_line, search_text, find_function"
    echo ""

    if [ -f "$STATE_FILE" ] && grep -q '"selection"' "$STATE_FILE" 2>/dev/null; then
        SELECTED_FILE=$(grep -o '"file_path": "[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
        START_LINE=$(grep -o '"start_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
        END_LINE=$(grep -o '"end_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
        if [ -n "$SELECTED_FILE" ]; then
            echo "📝 Selection: $SELECTED_FILE:$START_LINE-$END_LINE"
        fi
    else
        echo "ℹ️  No selection yet - select code in the browser to analyze"
    fi
}

case "${1:-}" in
    start)      cmd_start "${2:-}" ;;
    stop)       cmd_stop "${2:-}" ;;
    status)     cmd_status "${2:-}" ;;
    selection)  cmd_selection ;;
    setup)      cmd_setup ;;
    -h|--help|"") usage ;;
    *)
        echo "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
