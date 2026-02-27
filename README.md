# ContextViewerMCP

Interactive document visualization via MCP (Model Context Protocol). Enables Claude and other AI assistants to work with documents and code files through a visual selection interface.

---

## Quick Start

### 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/amokkapati/ContextViewerMCP/main/scripts/install.sh | sh
```

---

### 2. Add to PATH

```bash
echo 'export PATH="$HOME/.cache/contextviewermcp/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### 3. Set up MCP Integration(First Time)

```bash
cd ~/myproject
contextviewermcp --setup claudecode
```

---

### 4. Start the Server

```bash
contextviewermcp start
```

---

### 5. Enable in Claude Code

Open Claude Code in your project directory. 
```bash
claude
```
A prompt will appear asking if you want to use the MCP server defined in `.mcp.json` — click **Yes**.

---

### 6. Usage Examples

#### Selecting Content in the Web UI

- **Click and drag** — Select a range of lines
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
