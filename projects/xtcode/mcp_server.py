"""MCP Server layer for XTCode.

Exposes XTCode's tools via the Model Context Protocol (JSON-RPC over stdio).
Other MCP clients can connect and use XTCode's capabilities:
  read files, write files, edit, run commands, search, etc.

Usage:
  python -m projects.xtcode.mcp_server
  # or
  python projects/xtcode/mcp_server.py
"""

import json
import sys
import os
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Tool definitions exposed via MCP
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns the full text content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "start_line": {"type": "integer", "description": "Optional start line (1-indexed)"},
                "end_line": {"type": "integer", "description": "Optional end line (1-indexed, inclusive)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace a specific text span in a file. Use old_text to find the location and new_text as the replacement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_text": {"type": "string", "description": "Exact text to find"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "multi_edit",
        "description": "Apply multiple edits to a single file atomically. Each edit has old_text and new_text.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_text": {"type": "string"},
                            "new_text": {"type": "string"},
                        },
                        "required": ["old_text", "new_text"],
                    },
                    "description": "List of {old_text, new_text} pairs to apply in order",
                },
            },
            "required": ["path", "edits"],
        },
    },
    {
        "name": "bash",
        "description": "Run a shell command and return stdout/stderr.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)", "default": 30},
            },
            "required": ["command"],
        },
    },
    {
        "name": "search",
        "description": "Search file contents using ripgrep-style regex. Returns matching lines with file paths and line numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern (regex)"},
                "path": {"type": "string", "description": "Directory or file to search in", "default": "."},
                "include": {"type": "string", "description": "File glob pattern to include (e.g. '*.py')"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "glob",
        "description": "List files matching a glob pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
                "path": {"type": "string", "description": "Base directory", "default": "."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "web_fetch",
        "description": "Fetch the content of a URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web using a query string.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Max results to return", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "todo_read",
        "description": "Read the current task/todo list.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "todo_write",
        "description": "Update the task/todo list.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "done"]},
                        },
                        "required": ["task", "status"],
                    },
                },
            },
            "required": ["todos"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

TODO_FILE = os.path.join(os.path.dirname(__file__), ".xtcode_todo")


def _execute_mcp_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool and return MCP-formatted result."""
    try:
        result = _run_tool(name, args)
        return {"content": [{"type": "text", "text": str(result)}], "isError": False}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}


def _run_tool(name: str, args: dict[str, Any]) -> str:
    """Dispatch tool execution."""
    if name == "read_file":
        return _tool_read(args["path"], args.get("start_line"), args.get("end_line"))
    elif name == "write_file":
        return _tool_write(args["path"], args["content"])
    elif name == "edit_file":
        return _tool_edit(args["path"], args["old_text"], args["new_text"])
    elif name == "multi_edit":
        return _tool_multi_edit(args["path"], args["edits"])
    elif name == "bash":
        return _tool_bash(args["command"], args.get("timeout", 30))
    elif name == "search":
        return _tool_search(args["pattern"], args.get("path", "."), args.get("include"))
    elif name == "glob":
        return _tool_glob(args["pattern"], args.get("path", "."))
    elif name == "web_fetch":
        return _tool_web_fetch(args["url"])
    elif name == "web_search":
        return _tool_web_search(args["query"], args.get("num_results", 5))
    elif name == "todo_read":
        return _tool_todo_read()
    elif name == "todo_write":
        return _tool_todo_write(args["todos"])
    elif name == "list_directory":
        return _tool_list_dir(args.get("path", "."))
    else:
        raise ValueError(f"Unknown tool: {name}")


def _tool_read(path: str, start: int | None = None, end: int | None = None) -> str:
    with open(path) as f:
        lines = f.read