#!/bin/bash
# Stop the ContextViewer server

PORT=${1:-8765}

if lsof -i :$PORT > /dev/null 2>&1; then
    PID=$(lsof -ti :$PORT)
    kill $PID
    echo "✓ Stopped server on port $PORT (PID: $PID)"
else
    echo "No server running on port $PORT"
fi

# Clean up temporary state file
TMP_FILE="$HOME/.context-viewer-state.json.tmp"
if [ -f "$TMP_FILE" ]; then
    rm "$TMP_FILE"
    echo "✓ Cleaned up temporary state file"
fi

# Reset the context viewer state file
STATE_FILE="$HOME/.context-viewer-state.json"
echo "{}" > "$STATE_FILE"
echo "✓ Reset context viewer state file"
