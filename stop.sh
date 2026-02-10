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
