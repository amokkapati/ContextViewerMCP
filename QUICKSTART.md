# ContextViewer MCP - Quick Start Guide

This guide will walk you through your first interaction with ContextViewer MCP.

## Prerequisites

- ✅ Installed dependencies (`pip install -r requirements.txt` in a venv)
- ✅ Configured Claude Desktop (see INSTALL.md)
- ✅ Restarted Claude Desktop

## Tutorial: First Selection

### Step 1: Open the Viewer

In Claude Desktop, type:

```
Can you open the context viewer?
```

Claude will respond with a URL like `http://localhost:8765`. Click it or paste it in your browser.

### Step 2: Browse Files

In the web UI:
- You'll see a file browser on the left
- Click on `example_code.py` to open it
- The code will appear on the right with line numbers

### Step 3: Select Code

Let's select the `fibonacci` function:

1. Click on line 7 (the `def fibonacci(n):` line)
2. Hold Shift and click on line 16 (the last line of the function)
3. Lines 7-16 should now be highlighted in blue
4. Click the "✓ Confirm Selection" button at the top

### Step 4: Ask Claude About Your Selection

Go back to Claude Desktop and ask:

```
What does the code I selected do? Can you suggest improvements?
```

Claude will:
1. Automatically retrieve your selection using the `get_selection` tool
2. See the exact code you selected
3. Provide analysis and suggestions

### Step 5: Try Different Selection Methods

#### Paragraph Selection (Double-Click)

1. In the viewer, find a comment block
2. Double-click anywhere in the comment
3. The entire paragraph will be selected

#### Indent Block Selection (Alt/Option-Click)

1. Find an indented block (like a method in a class)
2. Hold Alt/Option and click on any line in the method
3. The entire indented block will be selected

#### Range Selection (Drag)

1. Click and hold on a line
2. Drag up or down
3. Release to select the range

## Example Workflows

### Workflow 1: Code Review

```
# In Claude Desktop
1. "Open the context viewer"
2. [In browser: select a function]
3. "Review this code for potential bugs and improvements"
```

### Workflow 2: Refactoring

```
# In Claude Desktop
1. "Open the context viewer"
2. [In browser: select the fibonacci function]
3. "Refactor this to use memoization for better performance"
4. [Claude provides refactored code]
5. "Can you show me how to test this?"
```

### Workflow 3: LaTeX Document Analysis

```
# In Claude Desktop
1. "Open the context viewer"
2. [In browser: click on main.tex]
3. [Select a section]
4. "Explain what this LaTeX code produces"
5. "Can you help me improve the formatting?"
6. [In browser: click 'Render PDF' button to see the result]
```

### Workflow 4: Documentation

```
# In Claude Desktop
1. "Open the context viewer"
2. [In browser: select a class]
3. "Generate comprehensive documentation for this class"
4. "Add type hints to the methods"
```

## Using Prompts

ContextViewer includes pre-built prompts for common tasks:

### Analyze Selection

```
# First, select code in the viewer
# Then in Claude:
Use the analyze-selection prompt
```

### Refactor Selection

```
# First, select code in the viewer
# Then in Claude:
Use the refactor-selection prompt with instructions: "use async/await"
```

### Explain LaTeX

```
# First, select LaTeX in the viewer
# Then in Claude:
Use the explain-latex prompt with focus: "mathematical notation"
```

## Tips and Tricks

### Selection Shortcuts

- **Single click**: Toggle line selection
- **Shift + click**: Select range from last clicked line
- **Double-click**: Select entire paragraph
- **Alt/Option + click**: Select indent block
- **Click and drag**: Select range

### Clearing Selection

Click the "✕ Clear Selection" button to start over.

### Multiple Selections

Currently, only one selection can be active at a time. Confirm your selection before making a new one.

### Working with Large Files

For large files:
1. Use Ctrl/Cmd+F to find specific sections
2. Use indent-block selection to grab entire functions/classes
3. Ask Claude to summarize before diving into details

## Advanced: Direct Tool Usage

You can also ask Claude to use tools directly:

### List Files

```
Can you list the files in this directory?
```

Claude will use the `list_files` tool.

### Read a Specific File

```
Can you read the contents of server.py?
```

Claude will use the `read_file` tool.

### Render LaTeX

```
Can you compile main.tex to PDF?
```

Claude will use the `render_latex` tool and provide a link to view the PDF.

## Troubleshooting

### Selection Not Showing Up

1. Make sure you clicked "✓ Confirm Selection"
2. Check that the confirmation message appeared
3. Try asking: "What's my current selection?"

### Viewer Won't Load

1. Check that the URL is correct (should be http://localhost:8765)
2. Try refreshing the page
3. Ask Claude to restart: "Can you restart the context viewer?"

### Code Not Highlighting Properly

The viewer uses Highlight.js for syntax highlighting. It should auto-detect:
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- LaTeX (.tex)
- Many other formats

If highlighting is wrong, it's usually still selectable.

## Next Steps

- Read the full README.md for architecture details
- Explore the example_code.py file
- Try with your own code files
- Experiment with LaTeX documents
- Check out the prompts in the MCP server

## Getting Help

If you run into issues:

1. Run the test suite: `python test_mcp.py`
2. Check the INSTALL.md troubleshooting section
3. Look at Claude Desktop logs for errors
4. Open an issue on GitHub (link TBD)

Happy coding with ContextViewer MCP! 🚀
