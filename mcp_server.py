#!/usr/bin/env python3
"""
ContextViewer MCP Server

Provides interactive document visualization with selection-based feedback.
Supports PDF/LaTeX documents and code files with a web-based UI.
"""

import asyncio
import json
import logging
import mimetypes
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
    Prompt,
    PromptMessage,
    GetPromptResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("context-viewer")

# Server instance
app = Server("context-viewer")

# State management
STATE_FILE = Path.home() / ".context-viewer-state.json"
HTTP_SERVER_PROCESS = None
BASE_DIR = Path.cwd()
HTTP_PORT = 8765


def get_state() -> dict[str, Any]:
    """Read the current state from the state file."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        # Validate state structure
        if not isinstance(state, dict):
            logger.warning("Invalid state file format, resetting")
            return {}

        # Validate selection structure if present
        if "selection" in state:
            sel = state["selection"]
            required_fields = ["file_path", "start_line", "end_line", "selected_text", "timestamp"]
            if not all(field in sel for field in required_fields):
                logger.warning("Invalid selection structure, removing")
                state.pop("selection", None)
                save_state(state)

        return state
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted state file: {e}, resetting")
        # Backup corrupted file
        backup_path = STATE_FILE.with_suffix(".json.backup")
        if STATE_FILE.exists():
            STATE_FILE.rename(backup_path)
            logger.info(f"Backed up corrupted state to {backup_path}")
        return {}
    except Exception as e:
        logger.error(f"Failed to read state: {e}")
        return {}


def save_state(state: dict[str, Any]) -> None:
    """Save state to the state file atomically."""
    try:
        # Write to temporary file first for atomic operation
        temp_file = STATE_FILE.with_suffix(".json.tmp")
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)

        # Atomic rename (overwrites existing file)
        temp_file.replace(STATE_FILE)
        logger.debug("State saved successfully")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def start_http_server() -> subprocess.Popen:
    """Start the HTTP server for the web UI."""
    global HTTP_SERVER_PROCESS
    if HTTP_SERVER_PROCESS is not None:
        return HTTP_SERVER_PROCESS

    logger.info(f"Starting HTTP server on port {HTTP_PORT}")
    HTTP_SERVER_PROCESS = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "server.py"), str(HTTP_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    logger.info(f"HTTP server started at http://localhost:{HTTP_PORT}")
    save_state({"server_url": f"http://localhost:{HTTP_PORT}", "server_pid": HTTP_SERVER_PROCESS.pid})

    return HTTP_SERVER_PROCESS


def stop_http_server() -> None:
    """Stop the HTTP server."""
    global HTTP_SERVER_PROCESS
    if HTTP_SERVER_PROCESS is not None:
        logger.info("Stopping HTTP server")
        HTTP_SERVER_PROCESS.terminate()
        try:
            HTTP_SERVER_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            HTTP_SERVER_PROCESS.kill()
        HTTP_SERVER_PROCESS = None


def list_files(path: str = "") -> list[dict[str, Any]]:
    """List files in a directory."""
    full_path = BASE_DIR / path.lstrip("/")
    full_path = full_path.resolve()

    if not str(full_path).startswith(str(BASE_DIR)):
        raise ValueError("Access denied: path outside base directory")

    if not full_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if not full_path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    items = []
    for item in sorted(full_path.iterdir()):
        if item.name.startswith("."):
            continue
        rel_path = item.relative_to(BASE_DIR)
        items.append({
            "name": item.name,
            "path": str(rel_path),
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else 0,
        })

    return items


def read_file(path: str) -> dict[str, Any]:
    """Read file content."""
    full_path = BASE_DIR / path.lstrip("/")
    full_path = full_path.resolve()

    if not str(full_path).startswith(str(BASE_DIR)):
        raise ValueError("Access denied: path outside base directory")

    if not full_path.is_file():
        raise ValueError(f"Not a file: {path}")

    mime_type, _ = mimetypes.guess_type(str(full_path))

    with open(full_path, "rb") as f:
        raw = f.read()

    is_text = b"\x00" not in raw
    content = None

    if is_text:
        content = raw.decode("utf-8", errors="replace")

    return {
        "content": content,
        "mime_type": mime_type,
        "is_text": is_text,
        "size": len(raw),
        "path": path,
    }


def render_latex(path: str) -> dict[str, Any]:
    """Render a LaTeX file to PDF."""
    full_path = BASE_DIR / path.lstrip("/")
    full_path = full_path.resolve()

    if not str(full_path).startswith(str(BASE_DIR)):
        raise ValueError("Access denied: path outside base directory")

    if not full_path.is_file() or not full_path.suffix == ".tex":
        raise ValueError(f"Not a .tex file: {path}")

    tex_dir = full_path.parent
    tex_filename = full_path.name
    pdf_filename = full_path.stem + ".pdf"
    pdf_path = tex_dir / pdf_filename

    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            cwd=tex_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Clean up auxiliary files
        for ext in [".aux", ".log"]:
            aux_file = tex_dir / (full_path.stem + ext)
            if aux_file.exists():
                aux_file.unlink()

        if result.returncode != 0 or not pdf_path.exists():
            error_msg = result.stderr or result.stdout or "pdflatex compilation failed"
            return {"success": False, "error": error_msg[:500]}

        rel_pdf_path = pdf_path.relative_to(BASE_DIR)
        return {
            "success": True,
            "pdf_path": str(rel_pdf_path),
            "pdf_url": f"http://localhost:{HTTP_PORT}/{rel_pdf_path}",
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Compilation timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "pdflatex not found. Please install LaTeX."}
    except Exception as e:
        return {"success": False, "error": str(e)}


# MCP Resources
@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available file resources."""
    # Return empty list for instant startup
    # Users can browse files via the list_files tool or web UI
    return []


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if not uri.startswith("file:///"):
        raise ValueError(f"Unsupported URI scheme: {uri}")

    path = uri.replace("file:///", "")
    file_data = read_file(path)

    if file_data["is_text"]:
        return file_data["content"]
    else:
        return f"Binary file: {path} ({file_data['size']} bytes, {file_data['mime_type']})"


# MCP Tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="open_viewer",
            description="Open the web-based file viewer UI. Returns the URL where the viewer is running. Users can select text/regions in the UI.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="list_files",
            description="List files in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (relative to project root, default: root)",
                    },
                },
            },
        ),
        Tool(
            name="read_file",
            description="Read the content of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to project root)",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="render_latex",
            description="Compile a LaTeX (.tex) file to PDF",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to .tex file (relative to project root)",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="get_selection",
            description="Get the current text selection from the web UI (if any). Returns the selected text, file path, and line numbers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "wait": {
                        "type": "boolean",
                        "description": "If true, wait for user to make a selection (default: false)",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum time to wait in seconds (default: 60)",
                    },
                    "clear_after_read": {
                        "type": "boolean",
                        "description": "If true, automatically clear the selection after reading (default: true in wait mode, false in immediate mode)",
                    },
                },
            },
        ),
        Tool(
            name="clear_selection",
            description="Clear the current selection state",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="navigate_to_line",
            description="Command the web viewer to navigate to a specific line in a file. The viewer will load the file, scroll to the line, and highlight it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to project root)",
                    },
                    "line": {
                        "type": "number",
                        "description": "Line number to navigate to",
                    },
                },
                "required": ["path", "line"],
            },
        ),
        Tool(
            name="navigate_to_text",
            description="Command the web viewer to search for text and navigate to the first occurrence. The viewer will load the file, find the text, scroll to it, and highlight it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to project root)",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to search for (can be partial match)",
                    },
                },
                "required": ["path", "text"],
            },
        ),
        Tool(
            name="navigate_to_function",
            description="Command the web viewer to find a function/class definition and navigate to it. The viewer will search for 'def function_name' or 'class ClassName' patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to project root)",
                    },
                    "name": {
                        "type": "string",
                        "description": "Function or class name to find",
                    },
                },
                "required": ["path", "name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "open_viewer":
            start_http_server()
            state = get_state()
            url = state.get("server_url", f"http://localhost:{HTTP_PORT}")
            return [
                TextContent(
                    type="text",
                    text=f"Web viewer is running at: {url}\n\nOpen this URL in your browser to select text from files. "
                    f"After making a selection and clicking 'Confirm Selection', use the 'get_selection' tool to retrieve it.",
                )
            ]

        elif name == "list_files":
            path = arguments.get("path", "")
            files = list_files(path)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(files, indent=2),
                )
            ]

        elif name == "read_file":
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required")

            file_data = read_file(path)
            if file_data["is_text"]:
                return [
                    TextContent(
                        type="text",
                        text=f"File: {path}\nMIME Type: {file_data['mime_type']}\n\n{file_data['content']}",
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Binary file: {path}\nMIME Type: {file_data['mime_type']}\nSize: {file_data['size']} bytes",
                    )
                ]

        elif name == "render_latex":
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required")

            result = render_latex(path)
            if result["success"]:
                return [
                    TextContent(
                        type="text",
                        text=f"LaTeX compiled successfully!\n\nPDF: {result['pdf_path']}\nView at: {result['pdf_url']}",
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"LaTeX compilation failed:\n\n{result['error']}",
                    )
                ]

        elif name == "get_selection":
            wait = arguments.get("wait", False)
            timeout = arguments.get("timeout", 60)
            # Default: auto-clear in wait mode, manual clear in immediate mode
            clear_after_read = arguments.get("clear_after_read", wait)

            if wait:
                # Polling mode - wait for new selection
                start_time = time.time()
                poll_count = 0
                logger.info(f"Polling for selection (timeout: {timeout}s)")

                while time.time() - start_time < timeout:
                    state = get_state()
                    selection = state.get("selection")
                    poll_count += 1

                    if selection and selection.get("timestamp", 0) > start_time:
                        elapsed = time.time() - start_time
                        logger.info(f"Selection found after {elapsed:.2f}s ({poll_count} polls)")

                        # Clear the selection after reading if requested
                        if clear_after_read:
                            state.pop("selection", None)
                            save_state(state)
                            logger.debug("Selection cleared after read")

                        return [
                            TextContent(
                                type="text",
                                text=f"Selection from: {selection['file_path']}\n"
                                f"Lines: {selection['start_line']}-{selection['end_line']}\n\n"
                                f"{selection['selected_text']}",
                            )
                        ]
                    await asyncio.sleep(0.5)

                logger.info(f"No selection within {timeout}s ({poll_count} polls)")
                return [
                    TextContent(
                        type="text",
                        text=f"No selection made within {timeout} seconds.",
                    )
                ]
            else:
                # Immediate mode - return current selection
                read_start = time.time()
                state = get_state()
                selection = state.get("selection")
                read_time = (time.time() - read_start) * 1000  # ms

                if not selection:
                    logger.debug(f"No selection available (read time: {read_time:.2f}ms)")
                    return [
                        TextContent(
                            type="text",
                            text="No selection available. Use 'open_viewer' to open the UI and make a selection, "
                            "or use wait=true to wait for a selection.",
                        )
                    ]

                logger.info(f"Selection retrieved in {read_time:.2f}ms")

                # Clear the selection after reading if requested
                if clear_after_read:
                    state.pop("selection", None)
                    save_state(state)
                    logger.debug("Selection cleared after read")

                return [
                    TextContent(
                        type="text",
                        text=f"Selection from: {selection['file_path']}\n"
                        f"Lines: {selection['start_line']}-{selection['end_line']}\n\n"
                        f"{selection['selected_text']}",
                    )
                ]

        elif name == "clear_selection":
            state = get_state()
            state.pop("selection", None)
            save_state(state)
            return [
                TextContent(
                    type="text",
                    text="Selection cleared.",
                )
            ]

        elif name == "navigate_to_line":
            path = arguments.get("path")
            line = arguments.get("line")
            if not path or line is None:
                raise ValueError("path and line are required")

            state = get_state()
            state["navigation"] = {
                "command": "goto_line",
                "file_path": path,
                "target": line,
                "timestamp": time.time(),
                "executed": False,
            }
            save_state(state)
            logger.info(f"Navigation command issued: goto line {line} in {path}")
            return [
                TextContent(
                    type="text",
                    text=f"Navigation command sent: Go to line {line} in {path}\n\n"
                    f"The web viewer will automatically navigate to this location if it's open.",
                )
            ]

        elif name == "navigate_to_text":
            path = arguments.get("path")
            text = arguments.get("text")
            if not path or not text:
                raise ValueError("path and text are required")

            state = get_state()
            state["navigation"] = {
                "command": "search_text",
                "file_path": path,
                "target": text,
                "timestamp": time.time(),
                "executed": False,
            }
            save_state(state)
            logger.info(f"Navigation command issued: search for '{text}' in {path}")
            return [
                TextContent(
                    type="text",
                    text=f"Navigation command sent: Search for '{text}' in {path}\n\n"
                    f"The web viewer will automatically navigate to the first occurrence if it's open.",
                )
            ]

        elif name == "navigate_to_function":
            path = arguments.get("path")
            name_arg = arguments.get("name")
            if not path or not name_arg:
                raise ValueError("path and name are required")

            state = get_state()
            state["navigation"] = {
                "command": "find_function",
                "file_path": path,
                "target": name_arg,
                "timestamp": time.time(),
                "executed": False,
            }
            save_state(state)
            logger.info(f"Navigation command issued: find function/class '{name_arg}' in {path}")
            return [
                TextContent(
                    type="text",
                    text=f"Navigation command sent: Find function/class '{name_arg}' in {path}\n\n"
                    f"The web viewer will automatically navigate to the definition if it's open.",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]


# MCP Prompts
@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="analyze-selection",
            description="Analyze a code or document selection from the viewer",
            arguments=[
                {
                    "name": "question",
                    "description": "What you want to know about the selection",
                    "required": False,
                }
            ],
        ),
        Prompt(
            name="refactor-selection",
            description="Refactor selected code with specific instructions",
            arguments=[
                {
                    "name": "instructions",
                    "description": "How to refactor the code",
                    "required": True,
                }
            ],
        ),
        Prompt(
            name="explain-latex",
            description="Explain a LaTeX document section",
            arguments=[
                {
                    "name": "focus",
                    "description": "What aspect to focus on (structure, content, formatting, etc.)",
                    "required": False,
                }
            ],
        ),
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """Get a prompt by name."""
    arguments = arguments or {}

    # Get current selection
    state = get_state()
    selection = state.get("selection")

    if not selection:
        return GetPromptResult(
            description="No selection available",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="Please open the viewer (use 'open_viewer' tool) and select some text first.",
                    ),
                )
            ],
        )

    if name == "analyze-selection":
        question = arguments.get("question", "What does this code/text do?")
        return GetPromptResult(
            description=f"Analyze selection from {selection['file_path']}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"I've selected the following from {selection['file_path']} "
                        f"(lines {selection['start_line']}-{selection['end_line']}):\n\n"
                        f"```\n{selection['selected_text']}\n```\n\n"
                        f"{question}",
                    ),
                )
            ],
        )

    elif name == "refactor-selection":
        instructions = arguments.get("instructions", "")
        if not instructions:
            return GetPromptResult(
                description="Missing refactoring instructions",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text="Please provide refactoring instructions in the 'instructions' argument.",
                        ),
                    )
                ],
            )

        return GetPromptResult(
            description=f"Refactor selection from {selection['file_path']}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Please refactor the following code from {selection['file_path']} "
                        f"(lines {selection['start_line']}-{selection['end_line']}):\n\n"
                        f"```\n{selection['selected_text']}\n```\n\n"
                        f"Instructions: {instructions}\n\n"
                        f"Provide the refactored code and explain the changes.",
                    ),
                )
            ],
        )

    elif name == "explain-latex":
        focus = arguments.get("focus", "content and structure")
        return GetPromptResult(
            description=f"Explain LaTeX from {selection['file_path']}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"I've selected the following LaTeX from {selection['file_path']} "
                        f"(lines {selection['start_line']}-{selection['end_line']}):\n\n"
                        f"```latex\n{selection['selected_text']}\n```\n\n"
                        f"Please explain this, focusing on: {focus}",
                    ),
                )
            ],
        )

    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    """Main entry point."""
    logger.info("Starting ContextViewer MCP Server")
    logger.info(f"Base directory: {BASE_DIR}")

    try:
        # HTTP server will start lazily when open_viewer tool is called
        # This speeds up initial MCP server startup

        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    finally:
        # Cleanup
        stop_http_server()
        logger.info("ContextViewer MCP Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
