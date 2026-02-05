#!/bin/bash
# Helper script to get the current selection from context viewer

STATE_FILE="$HOME/.context-viewer-state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "No selection available. Open http://localhost:8765 and select some text."
    exit 1
fi

# Extract and display the selection using jq if available, otherwise use Python
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
