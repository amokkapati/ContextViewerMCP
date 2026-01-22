# Installation Guide for ContextViewer MCP

## Quick Start

### 1. Set up Python Virtual Environment

```bash
# Navigate to the project directory
cd /Users/adityamokkapati/ContextViewerMCP

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Install LaTeX (Optional, for PDF rendering)

**macOS:**
```bash
brew install --cask mactex-no-gui
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra
```

**Fedora/RHEL:**
```bash
sudo dnf install texlive-scheme-basic
```

### 3. Test the Installation

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the test suite
python test_mcp.py
```

### 4. Configure Claude Desktop

Add the MCP server to Claude Desktop's configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this configuration (update paths to match your setup):

```json
{
  "mcpServers": {
    "context-viewer": {
      "command": "/Users/adityamokkapati/ContextViewerMCP/venv/bin/python",
      "args": [
        "/Users/adityamokkapati/ContextViewerMCP/mcp_server.py"
      ]
    }
  }
}
```

**Important:** Use the absolute path to the Python interpreter in your virtual environment!

### 5. Restart Claude Desktop

After updating the config file, restart Claude Desktop completely for the changes to take effect.

## Verification

### Test the HTTP Server Standalone

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python server.py 8000

# Open in browser
open http://localhost:8000
```

You should see the file browser UI. You can:
- Browse files in the sidebar
- Click on files to view them
- Select text by clicking lines
- Use Shift+click for range selection
- Use Alt/Option+click for indent block selection
- Double-click for paragraph selection

### Test with Claude Desktop

Once configured:

1. Open Claude Desktop
2. Start a new conversation
3. Ask: "Can you open the context viewer?"
4. Claude should respond with a URL to open
5. Open the URL in your browser
6. Select some text and click "Confirm Selection"
7. Ask Claude: "What did I select?"

## Troubleshooting

### "mcp module not found"

Make sure you're using the Python from the virtual environment:

```bash
# Check which Python you're using
which python

# Should point to: /Users/adityamokkapati/ContextViewerMCP/venv/bin/python
```

If not, activate the virtual environment:

```bash
source venv/bin/activate
```

### Claude Desktop doesn't see the server

1. Double-check the paths in `claude_desktop_config.json` are absolute paths
2. Verify the Python path points to the venv Python:
   ```bash
   ls -l /Users/adityamokkapati/ContextViewerMCP/venv/bin/python
   ```
3. Check Claude Desktop logs for errors
4. Make sure you completely restarted Claude Desktop (Quit and reopen, not just close window)

### Port already in use

If port 8765 is already in use, edit `mcp_server.py` and change the `HTTP_PORT` variable:

```python
HTTP_PORT = 8766  # Or any other available port
```

### LaTeX rendering fails

1. Verify pdflatex is installed and in PATH:
   ```bash
   which pdflatex
   pdflatex --version
   ```

2. On macOS, you may need to add to PATH:
   ```bash
   export PATH="/Library/TeX/texbin:$PATH"
   ```

3. Test LaTeX manually:
   ```bash
   cd /Users/adityamokkapati/ContextViewerMCP
   pdflatex main.tex
   ```

### Permission denied errors

Make sure the scripts are executable:

```bash
chmod +x mcp_server.py test_mcp.py
```

## Alternative: System-wide Installation

If you prefer not to use a virtual environment (not recommended):

```bash
# On macOS with Homebrew Python
pip3 install --user mcp

# Update Claude config to use system Python
{
  "mcpServers": {
    "context-viewer": {
      "command": "/usr/local/bin/python3",
      "args": ["/Users/adityamokkapati/ContextViewerMCP/mcp_server.py"]
    }
  }
}
```

## Next Steps

Once installed, see the main README.md for usage instructions and examples.
