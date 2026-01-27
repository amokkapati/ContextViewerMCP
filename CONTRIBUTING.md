# Contributing to ContextViewer MCP

Thank you for your interest in contributing! This document explains the architecture and how to extend the system.

## Architecture Deep Dive

### Component Diagram

```
┌───────────────────────────────────────────────────────────┐
│                     Claude Desktop                         │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  MCP Client                                       │    │
│  │  - Sends JSON-RPC requests over stdio            │    │
│  │  - Calls tools, reads resources, uses prompts    │    │
│  └─────────────────────┬────────────────────────────┘    │
└────────────────────────┼───────────────────────────────────┘
                         │
                         │ stdio (JSON-RPC)
                         │
┌────────────────────────▼───────────────────────────────────┐
│                   mcp_server.py                            │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  MCP Server (from mcp.server)                    │    │
│  │                                                   │    │
│  │  @app.list_resources()                           │    │
│  │  @app.read_resource()                            │    │
│  │  @app.list_tools()                               │    │
│  │  @app.call_tool()                                │    │
│  │  @app.list_prompts()                             │    │
│  │  @app.get_prompt()                               │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Process Management                               │    │
│  │  - start_http_server() → subprocess.Popen        │    │
│  │  - stop_http_server()                            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  State Management                                 │    │
│  │  - get_state() → reads JSON                      │    │
│  │  - save_state() → writes JSON                    │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────┬───────────────────────────────────┘
                         │
                         │ subprocess
                         │
┌────────────────────────▼───────────────────────────────────┐
│                      server.py                             │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  HTTP Server (SimpleHTTPRequestHandler)          │    │
│  │                                                   │    │
│  │  GET /                → HTML UI                  │    │
│  │  GET /api/files       → List files               │    │
│  │  GET /api/file-content→ Read file                │    │
│  │  GET /api/render-tex  → Compile LaTeX            │    │
│  │  POST /api/confirm-selection → Save selection    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Embedded HTML/JS UI                              │    │
│  │  - File tree with navigation                     │    │
│  │  - Code viewer with Highlight.js                 │    │
│  │  - Selection handling                            │    │
│  │  - LaTeX rendering toggle                        │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────┬───────────────────────────────────┘
                         │
                         │ HTTP (localhost:8765)
                         │
┌────────────────────────▼───────────────────────────────────┐
│                    Web Browser                             │
│                                                            │
│  User interacts with:                                     │
│  - File tree sidebar                                      │
│  - Code/document viewer                                   │
│  - Selection controls                                     │
│  - LaTeX render button                                    │
└────────────────────────────────────────────────────────────┘

State Synchronization:
~/.context-viewer-state.json (JSON file)
```

### Data Flow: Selection Workflow

```
1. User clicks "✓ Confirm Selection" in browser
   ↓
2. JavaScript sends POST to /api/confirm-selection
   {
     file_path: "example.py",
     start_line: 10,
     end_line: 20,
     selected_text: "..."
   }
   ↓
3. server.py saves to ~/.context-viewer-state.json
   {
     "selection": {
       "file_path": "example.py",
       "start_line": 10,
       "end_line": 20,
       "selected_text": "...",
       "timestamp": 1234567890.123
     }
   }
   ↓
4. User asks Claude: "What did I select?"
   ↓
5. Claude calls get_selection tool
   ↓
6. mcp_server.py reads ~/.context-viewer-state.json
   ↓
7. Returns selection to Claude
   ↓
8. Claude responds with analysis
```

## Adding New Features

### 1. Adding a New MCP Tool

Tools are functions that Claude can call. Here's how to add one:

```python
# In mcp_server.py

# Step 1: Add to list_tools()
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ... existing tools ...
        Tool(
            name="your_new_tool",
            description="What your tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of param1",
                    },
                    "param2": {
                        "type": "number",
                        "description": "Description of param2",
                    },
                },
                "required": ["param1"],
            },
        ),
    ]

# Step 2: Handle in call_tool()
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "your_new_tool":
        param1 = arguments.get("param1")
        param2 = arguments.get("param2", default_value)

        # Your tool logic here
        result = do_something(param1, param2)

        return [
            TextContent(
                type="text",
                text=f"Result: {result}",
            )
        ]
```

### 2. Adding a New MCP Prompt

Prompts are templates for common interactions:

```python
# In mcp_server.py

# Step 1: Add to list_prompts()
@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        # ... existing prompts ...
        Prompt(
            name="your-prompt",
            description="What this prompt helps with",
            arguments=[
                {
                    "name": "arg1",
                    "description": "Description of arg1",
                    "required": True,
                }
            ],
        ),
    ]

# Step 2: Handle in get_prompt()
@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    if name == "your-prompt":
        arg1 = arguments.get("arg1", "")
        state = get_state()
        selection = state.get("selection")

        return GetPromptResult(
            description=f"Your prompt description",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Your prompt text with {arg1}",
                    ),
                )
            ],
        )
```

### 3. Adding a New HTTP API Endpoint

To add functionality to the web UI:

```python
# In server.py

class FileServerHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # Add your endpoint
        if self.path.startswith("/api/your-endpoint"):
            self.handle_your_endpoint()
            return

        # ... existing endpoints ...

    def handle_your_endpoint(self):
        """Handle your new endpoint."""
        try:
            # Your logic here
            data = {"result": "success"}

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        except Exception as e:
            self.send_error(500)
```

### 4. Extending the Web UI

The HTML/JS is embedded in `server.py` in the `get_html()` method:

```python
def get_html(self):
    return """<!DOCTYPE html>
    <html>
    <head>
        <!-- Add your CSS here -->
        <style>
            .your-new-class {
                /* styles */
            }
        </style>
    </head>
    <body>
        <!-- Add your HTML here -->

        <script>
            // Add your JavaScript here
            async function yourNewFunction() {
                const res = await fetch('/api/your-endpoint');
                const data = await res.json();
                // Handle response
            }
        </script>
    </body>
    </html>"""
```

## Development Workflow

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repo-url>
cd ContextViewerMCP

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install black flake8 mypy
```

### Testing Changes

```bash
# Run the test suite
python test_mcp.py

# Test HTTP server standalone
python server.py 8000

# Test MCP server (requires MCP client)
# Add to Claude Desktop config and test there
```

### Code Style

- Use Black for formatting: `black *.py`
- Use type hints where appropriate
- Add docstrings to functions
- Keep line length under 100 characters
- Follow PEP 8

## Common Extension Scenarios

### Scenario 1: Add Support for a New File Type

**Example: Add Markdown preview**

1. Update `server.py` to detect .md files:

```python
def handle_file_content_api(self):
    # ... existing code ...
    if full_path.suffix == '.md':
        # Convert markdown to HTML
        html_content = markdown_to_html(content)
        return {
            "content": content,
            "html": html_content,
            "is_text": True,
        }
```

2. Update the UI to render HTML:

```javascript
function displayFile(data, name) {
    if (name.endsWith('.md') && data.html) {
        content.innerHTML = `<div class="markdown-preview">${data.html}</div>`;
        return;
    }
    // ... existing code ...
}
```

### Scenario 2: Add Real-Time Collaboration

**Replace file-based state with WebSocket:**

1. Add WebSocket support to `server.py`:

```python
import asyncio
import websockets

# Global set of connected clients
clients = set()

async def handle_websocket(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in clients]
            )
    finally:
        clients.remove(websocket)
```

2. Update `mcp_server.py` to use WebSocket:

```python
async def get_selection_realtime():
    async with websockets.connect('ws://localhost:8765/ws') as ws:
        message = await ws.recv()
        return json.loads(message)
```

### Scenario 3: Add Authentication

**Add basic auth to the HTTP server:**

```python
import base64

class FileServerHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # Check authentication
        auth_header = self.headers.get('Authorization')
        if not self.check_auth(auth_header):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="ContextViewer"')
            self.end_headers()
            return

        # ... existing code ...

    def check_auth(self, auth_header):
        if not auth_header:
            return False

        # Decode basic auth
        try:
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':')
            return username == "user" and password == "pass"
        except:
            return False
```

## Testing Guidelines

### Unit Tests

Create `tests/test_mcp_server.py`:

```python
import pytest
from mcp_server import list_files, read_file

def test_list_files():
    files = list_files("")
    assert isinstance(files, list)
    assert all("name" in f for f in files)

def test_read_file():
    data = read_file("README.md")
    assert data["is_text"] is True
    assert "content" in data
```

### Integration Tests

Create `tests/test_integration.py`:

```python
import subprocess
import time
import requests

def test_http_server_starts():
    proc = subprocess.Popen(["python", "server.py", "9999"])
    time.sleep(2)

    # Test that server responds
    resp = requests.get("http://localhost:9999/")
    assert resp.status_code == 200

    proc.terminate()
```

## Performance Considerations

### File Listing Optimization

For large directories:

```python
def list_files(path: str = "", max_items: int = 1000) -> list[dict]:
    """List files with a limit."""
    items = []
    for i, item in enumerate(sorted(full_path.iterdir())):
        if i >= max_items:
            break
        # ... process item ...
    return items
```

### Caching

Add caching for frequently accessed files:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def read_file_cached(path: str) -> dict:
    return read_file(path)
```

## Security Considerations

### Path Traversal Prevention

Always validate paths:

```python
def safe_path(user_path: str) -> Path:
    full_path = (BASE_DIR / user_path.lstrip("/")).resolve()

    # Ensure path is within BASE_DIR
    if not str(full_path).startswith(str(BASE_DIR)):
        raise ValueError("Path outside base directory")

    return full_path
```

### Input Validation

Validate all user inputs:

```python
def validate_line_numbers(start: int, end: int, max_lines: int):
    if start < 1 or end < 1:
        raise ValueError("Line numbers must be positive")
    if start > end:
        raise ValueError("Start line must be <= end line")
    if end > max_lines:
        raise ValueError(f"Line {end} exceeds file length")
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.debug("Debug message here")
```

### Debugging MCP Communication

The MCP protocol uses stdio, so you can't use print statements. Use logging instead:

```python
logger.info(f"Tool called: {name} with {arguments}")
```

### Common Issues

1. **Port already in use**: Change `HTTP_PORT` in `mcp_server.py`
2. **State file permission denied**: Check file permissions
3. **LaTeX not found**: Ensure pdflatex is in PATH
4. **MCP server not responding**: Check Claude Desktop logs

## Pull Request Guidelines

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Write tests**: Add tests for new functionality
3. **Update documentation**: Update relevant .md files
4. **Run tests**: Ensure `python test_mcp.py` passes
5. **Format code**: Run `black *.py`
6. **Create PR**: With clear description of changes

## Questions?

- Check the documentation files (README.md, INSTALL.md, QUICKSTART.md)
- Run the test suite: `python test_mcp.py`
- Open an issue on GitHub

Thank you for contributing! 🎉
