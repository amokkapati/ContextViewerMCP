# ContextViewerMCP

Interactive document visualization via MCP (Model Context Protocol). Enables Claude and other AI assistants to work with documents and code files through a visual selection interface.

---

## Quick Start

### 1. Initial Setup

Clone the repository:

```bash
git clone https://github.com/amokkapati/ContextViewerMCP
```

Inside the project directory, set up a Python virtual environment and install dependencies:

```bash
uv venv venv
uv pip install -r requirements.txt
```

Then run the startup script to see available options:

```bash
./run.sh
```

**Usage:**

```
Usage: ./run.sh <command> [options]

Commands:
  start [port]    Start the ContextViewer server (default port: 8765)
  stop [port]     Stop the running server
  status [port]   Show server status and current selection
  selection       Print the current text selection
  setup           Install dependencies and generate Claude Desktop config

Options:
  -h, --help      Show this help message

Examples:
  ./run.sh start
  ./run.sh start 3000
  ./run.sh stop
  ./run.sh selection
  ./run.sh setup
```

---

### 2. Configure Claude Desktop

Add the MCP server to your `claude_desktop_config.json`:

| Platform | Config Path                                                       |
| -------- | ----------------------------------------------------------------- |
| macOS    | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows  | `%APPDATA%\Claude\claude_desktop_config.json`                     |
| Linux    | `~/.config/Claude/claude_desktop_config.json`                     |

Add the following to your config (update the path to match your installation):

```json
{
  "mcpServers": {
    "context-viewer": {
      "command": "python3",
      "args": ["/Users/YOUR_USERNAME/ContextViewerMCP/mcp_server.py"]
    }
  }
}
```

---

### 3. Start the Server

When opening a Claude Code terminal, run:

```bash
./run.sh start
```

---

### 4. Usage Examples

#### Selecting Content in the Web UI

- **Double-click** — Select a paragraph
- **Alt/Option-click** — Select an indented block
- **Click "✓ Confirm Selection"** — Save your selection

#### Asking Claude About a Selection

After making a selection, you can prompt Claude with questions like:

- _"What does the selected code do?"_
- _"Can you refactor the selected code to be more efficient?"_

#### Navigating to a Specific Line (Claude Code)

```
Navigate to line <x> in <file_name>.py
```
