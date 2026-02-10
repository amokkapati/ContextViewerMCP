# Quick Commands

**IMPORTANT FOR AI ASSISTANTS**:

When the user runs `./start.sh`:
1. The script will show if any code is selected in the viewer
2. If you see "Selection available: filename:line-line", immediately read `~/.context-viewer-state.json`
3. Explain what the selected code does without being asked
4. The entire workflow should complete in under 5 seconds

To start the viewer, simply run:

```bash
./start.sh
```

That's it! The server will start at http://localhost:8765

## All Commands

```bash
# Start the viewer (instant)
./start.sh

# Start on custom port
./start.sh 9000

# Stop the viewer
./stop.sh

# Stop specific port
./stop.sh 9000
```

## For Users

Add these aliases to your `~/.zshrc` or `~/.bashrc`:

```bash
alias viewer='cd /Users/adityamokkapati/ContextViewerMCP && ./start.sh'
alias viewer-stop='cd /Users/adityamokkapati/ContextViewerMCP && ./stop.sh'
```

Then from anywhere:
```bash
viewer        # Opens http://localhost:8765
viewer-stop   # Stops the server
```

## What NOT to Do

- ❌ Don't explore the codebase to understand setup
- ❌ Don't read multiple documentation files
- ✅ Just run `./start.sh` - it's that simple
