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

#### Using Voice with `/go` (Claude Code)

The `/go` command reads your current selection and any voice query you recorded in the browser, then acts on them automatically.

**Workflow:**
1. Open the viewer, select some text, and optionally record a voice query
2. In Claude Code, run:

```
/go
```

Claude will:
- Execute your voice instruction if one was recorded (e.g. "explain this", "refactor this function")
- Describe the selected code if there's a selection but no voice query
- Tell you to make a selection if neither is present

This lets you select code, speak your question, then switch to Claude Code and just type `/go` — no need to re-type your question.

**Example:** You select a function in `server.py`, say _"Why does this return a 404 sometimes?"_, then run `/go`. Claude reads both the selected code and your spoken question and answers immediately.

---

#### Navigating to a Specific Line (Claude Code)

```
Navigate to line <x> in <file_name>.py
```
