# ContextViewerMCP

Interactive document visualization via MCP (Model Context Protocol). Enables Claude and other AI assistants to work with documents and code files through a visual selection interface.

---

## Quick Start

### 1. Initial Setup

Run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/amokkapati/ContextViewerMCP/main/scripts/install.sh | sh
```

Then add the CLI to your PATH:

```bash
echo 'export PATH="$HOME/.cache/contextviewermcp/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Usage:**

```
Usage: contextviewermcp <command> [options]

Commands:
  start [port]             Start the viewer (serves files from current directory)
  stop [port]              Stop the running server
  status [port]            Show server status and current selection
  selection                Print the current text selection
  --setup claudecode       Create .mcp.json for Claude Code MCP integration
  --setup claudedesktop    Update Claude Desktop config

Options:
  -h, --help               Show this help message

Examples:
  cd ~/myproject && contextviewermcp start
  contextviewermcp --setup claudecode
  contextviewermcp selection
```

---

### 2. Configure Claude Desktop or Claude Code

Run the setup command from your project directory:

```bash
cd ~/myproject
contextviewermcp --setup claudecode      # creates .mcp.json for Claude Code
contextviewermcp --setup claudedesktop   # updates Claude Desktop config
```

---

### 3. Start the Server

When opening a Claude Code terminal, run:

```bash
contextviewermcp start
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
