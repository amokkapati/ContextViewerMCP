# ContextViewerMCP

Interactive document visualization via MCP (Model Context Protocol). Enables Claude and other AI assistants to work with documents and code files through a visual selection interface.

## Quick Start

The easiest way to run ContextViewer is using the `start.sh` script:

### Prerequisites

To run `start.sh`, you need:

1. **Python 3** - Check if installed:
   ```bash
   python3 --version
   ```
   If not installed:
   - **macOS:** `brew install python3` or download from [python.org](https://www.python.org/downloads/)
   - **Linux:** `sudo apt-get install python3` (Ubuntu/Debian) or `sudo yum install python3` (RHEL/CentOS)

2. **pip** (Python package manager) - Usually comes with Python 3:
   ```bash
   pip3 --version
   ```

3. **MCP SDK** - Install the Python MCP library:
   ```bash
   pip install -r requirements.txt
   ```
   Or directly:
   ```bash
   pip install mcp
   ```

4. **Standard Unix tools** (included by default on macOS/Linux):
   - `bash` - Shell to run the script
   - `lsof` - To check if server is already running
   - `grep` - To parse state files

### Running the Server

Once prerequisites are installed:

```bash
# Make the script executable (first time only)
chmod +x start.sh

# Start the server on default port (8765)
./start.sh

# Or specify a custom port
./start.sh 3000
```

The script will:
- Check if a server is already running
- Start the server if needed
- Display the URL to open in your browser (e.g., `http://localhost:8765`)
- Show any existing text selections

### Stopping the Server

```bash
./stop.sh
```

## Features

- **Web-based viewer** for documents and code files with syntax highlighting
- **Interactive selection** - point, click, and select regions of text
- **LaTeX support** - render `.tex` files to PDF on-the-fly
- **MCP integration** - expose files, selections, and tools to AI assistants
- **Multi-format support** - PDF, LaTeX, code files (Python, JavaScript, TypeScript, etc.)

## Installation

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install LaTeX compiler (for PDF rendering)
brew install --cask mactex-no-gui  # macOS
# or for Linux:
# sudo apt-get install texlive-latex-base texlive-latex-extra
```

### 2. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this to your config (update the path to match your installation):

```json
{
  "mcpServers": {
    "context-viewer": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USERNAME/ContextViewerMCP/mcp_server.py"
      ]
    }
  }
}
```

### 3. Restart Claude Desktop

After updating the config, restart Claude Desktop for the changes to take effect.

## Usage

### Using with Claude Desktop

Once configured, Claude can use the following capabilities:

#### 1. Open the Viewer

Ask Claude to open the viewer:
```
Can you open the context viewer?
```

Claude will provide a URL (e.g., `http://localhost:8765`). Open this in your browser to see the file viewer.

#### 2. Browse and Select Files

In the web UI:
- Click files in the sidebar to view them
- Click lines to select them (hold Shift for range selection)
- Drag to select multiple lines
- Double-click to select a paragraph
- Alt/Option-click to select an indented block
- Click "✓ Confirm Selection" to save your selection

#### 3. Ask Claude About Selections

After making a selection, ask Claude:
```
What does this code do?
Can you refactor this to be more efficient?
Explain this LaTeX section
```

Claude will automatically access your selection using the `get_selection` tool.

#### 4. Using Prompts

Claude has access to pre-built prompts:
- **analyze-selection** - Analyze selected code or text
- **refactor-selection** - Refactor code with instructions
- **explain-latex** - Explain LaTeX document sections

Example:
```
Use the refactor-selection prompt with instructions: "convert to async/await"
```

#### 5. Bidirectional Navigation

Claude can now command the viewer to navigate to specific locations:

**Navigate to a line:**
```
Can you show me line 42 in example.py?
```

**Find and show text:**
```
Show me where "handleUserInput" appears in the code
```

**Jump to a function:**
```
Navigate to the function named processData
```

The viewer will automatically load the file, scroll to the location, and highlight it with a flash animation.

### Available MCP Tools

Claude has access to these tools:

**File Operations:**
- `open_viewer` - Start the web viewer UI
- `list_files` - List files in a directory
- `read_file` - Read file contents
- `render_latex` - Compile a .tex file to PDF

**Selection (User → Claude):**
- `get_selection` - Get the current selection from the UI
- `clear_selection` - Clear the selection state

**Bidirectional Navigation (Claude → Viewer):**
- `navigate_to_line` - Command the viewer to navigate to a specific line
- `navigate_to_text` - Command the viewer to search for text and navigate to it
- `navigate_to_function` - Command the viewer to find and navigate to a function/class definition

### Standalone Usage (without MCP)

You can also run the web viewer independently:

```bash
python3 server.py [PORT]
# Default port is 8000
```

Then open `http://localhost:8000` in your browser.

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│   (MCP Client)  │
└────────┬────────┘
         │ MCP Protocol (stdio)
         │
┌────────▼────────┐
│   mcp_server.py │  ← Main MCP server
│                 │  - Manages HTTP server
│                 │  - Exposes tools/resources
│                 │  - Reads selection state
└────────┬────────┘
         │ subprocess
         │
┌────────▼────────┐
│    server.py    │  ← HTTP/Web server
│                 │  - Serves web UI
│                 │  - Handles file API
│                 │  - Saves selections
└────────┬────────┘
         │
┌────────▼────────┐
│  Web Browser    │  ← User interface
│   (localhost)   │  - File browser
│                 │  - Text selection
│                 │  - PDF viewer
└─────────────────┘

State synchronization via:
~/.context-viewer-state.json
```

## Development

### Project Structure

```
ContextViewerMCP/
├── mcp_server.py              # MCP server implementation
├── server.py                  # HTTP server with web UI
├── requirements.txt           # Python dependencies
├── claude_desktop_config.json # Example Claude Desktop config
└── README.md                  # This file
```

### State Management

Selections are synchronized via a JSON state file at `~/.context-viewer-state.json`:

```json
{
  "server_url": "http://localhost:8765",
  "server_pid": 12345,
  "selection": {
    "file_path": "example.py",
    "start_line": 10,
    "end_line": 20,
    "selected_text": "...",
    "timestamp": 1234567890.123
  }
}
```

## Troubleshooting

### MCP server not appearing in Claude Desktop

1. Check that the path in `claude_desktop_config.json` is correct (use absolute path)
2. Verify Python 3 is installed: `python3 --version`
3. Check Claude Desktop logs for errors
4. Make sure you restarted Claude Desktop after config changes

### LaTeX rendering not working

1. Verify `pdflatex` is installed: `pdflatex --version`
2. On macOS, ensure `/Library/TeX/texbin` is in your PATH
3. Check for LaTeX compilation errors in the web UI

### Web viewer won't open

1. Check if another process is using port 8765
2. Try a different port by modifying `HTTP_PORT` in `mcp_server.py`
3. Check firewall settings

### Selection not appearing in Claude

1. Make sure you clicked "✓ Confirm Selection" in the web UI
2. Check that `~/.context-viewer-state.json` exists and contains your selection
3. Try using `get_selection` tool with `wait: true`

## Contributing

Contributions are welcome! This project is part of a UCSC research project on interactive document visualization for AI assistants.

### Team
- Aditya Mokkapati (amokkapa@ucsc.edu)
- Anish Nutakki (annutakk@ucsc.edu)

## License

[Add license information]
