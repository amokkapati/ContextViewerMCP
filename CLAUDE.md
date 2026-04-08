# ContextViewerMCP

A web-based file/PDF viewer that lets users select code or text in the browser, then ask Claude about it.

## On conversation start

1. Check `~/.context-viewer-state.json` for a current selection. If one exists, announce the file and line range so the user knows you can see it.
2. Check if the viewer server is running on port 8765. If not, remind the user to run `contextviewermcp start`.

## Workflow

- User runs `contextviewermcp start` → opens browser at http://localhost:8765
- User selects text in the browser and clicks "Confirm Selection"
- Selection is saved to `~/.context-viewer-state.json`
- User asks Claude a question → Claude reads the state file to get the selected text

## Responding to selections and voice queries

When the user asks you to check the selection or answer a voice query, call `get_selection` with **`wait: false`** (not `wait: true`) to read whatever is already in the state file. Do NOT use `wait: true` unless the user explicitly asks you to wait for them to make a new selection. The intended workflow is: user selects + speaks in browser first, then asks Claude — so the selection already exists when Claude is asked.

## Key files

- `server.py` — HTTP server serving the browser UI (accepts `--serve-dir PATH`)
- `mcp_server.py` — MCP server for Claude integration (accepts `--serve-dir PATH`)
- `contextviewermcp` — CLI entry point (always serves from `$PWD`)
- `~/.context-viewer-state.json` — shared state: current selection + navigation commands

## MCP tools available

- `get_selection` — read current selection from state file
- `open_viewer` — get the viewer URL
- `navigate_to_line` / `navigate_to_text` / `navigate_to_function` — scroll the browser to a location
- `list_files` / `read_file` — browse project files
- `render_latex` — compile a .tex file to PDF
