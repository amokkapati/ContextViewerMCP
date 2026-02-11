#!/bin/bash
# Quick launch script for ContextViewer
# Usage: ./start.sh [port]

PORT=${1:-8765}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Check if server is already running
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ Server already running at http://localhost:$PORT"
    echo ""
    echo "💡 Claude: Read mcp_server.py to understand available MCP tools and capabilities"
    echo "💡 Claude: ALWAYS check ~/.context-viewer-state.json when asked about selected code or selections"
    echo "💡 Claude: When user says 'show me line X in file.py', use navigate_to_line tool to display it in the web viewer"
    echo ""

    # Check for selections
    STATE_FILE="$HOME/.context-viewer-state.json"
    if [ -f "$STATE_FILE" ]; then
        if grep -q '"selection"' "$STATE_FILE" 2>/dev/null; then
            SELECTED_FILE=$(grep -o '"file_path": "[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
            START_LINE=$(grep -o '"start_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
            END_LINE=$(grep -o '"end_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
            if [ -n "$SELECTED_FILE" ]; then
                echo "📝 Selection available: $SELECTED_FILE:$START_LINE-$END_LINE"
            fi
        else
            echo "ℹ️  No selection yet - select code in browser to analyze"
        fi
    fi
    exit 0
fi

# Start server
echo "Starting ContextViewer on port $PORT..."
python3 server.py $PORT > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
sleep 1

if lsof -i :$PORT > /dev/null 2>&1; then
    echo "✓ Server started at http://localhost:$PORT"
    echo "  PID: $SERVER_PID"
    echo ""
    echo "💡 Claude: Read mcp_server.py to understand available MCP tools and capabilities"
    echo "💡 Claude: ALWAYS check ~/.context-viewer-state.json when asked about selected code or selections"
    echo "💡 Claude: When user says 'show me line X in file.py', use navigate_to_line tool to display it in the web viewer"
    echo ""

    # Check for selections
    STATE_FILE="$HOME/.context-viewer-state.json"
    if [ -f "$STATE_FILE" ]; then
        if grep -q '"selection"' "$STATE_FILE" 2>/dev/null; then
            SELECTED_FILE=$(grep -o '"file_path": "[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
            START_LINE=$(grep -o '"start_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
            END_LINE=$(grep -o '"end_line": [0-9]*' "$STATE_FILE" | cut -d' ' -f2)
            if [ -n "$SELECTED_FILE" ]; then
                echo "📝 Selection available: $SELECTED_FILE:$START_LINE-$END_LINE"
            fi
        else
            echo "ℹ️  No selection yet - select code in browser to analyze"
        fi
    fi
    echo ""
    echo "To stop: ./stop.sh or kill $SERVER_PID"
else
    echo "✗ Failed to start server"
    exit 1
fi
