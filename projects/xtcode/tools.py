"""XTCode tool definitions and execution engine."""
import os
import subprocess
import glob
import re
from pathlib import Path
try:
    from config import WORKSPACE_ROOT, SHELL_TIMEOUT, MAX_FILE_LINES
except ImportError:
    from .config import WORKSPACE_ROOT, SHELL_TIMEOUT, MAX_FILE_LINES


# ── Tool Definitions (sent to LLM) ──────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns line-numbered content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "start_line": {"type": "integer", "description": "First line to read (1-indexed, optional)"},
                "end_line": {"type": "integer", "description": "Last line to read (inclusive, optional)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace a specific range of lines in a file. Lines are 1-indexed, inclusive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "start_line": {"type": "integer", "description": "First line to replace (1-indexed)"},
                "end_line": {"type": "integer", "description": "Last line to replace (inclusive)"},
                "new_content": {"type": "string", "description": "Replacement content"},
            },
            "required": ["path", "start_line", "end_line", "new_content"],
        },
    },
    {
        "name": "run_command",
        "description": "Execute a shell command in the workspace directory. Returns stdout, stderr, and exit code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": f"Timeout in seconds (default: {SHELL_TIMEOUT})"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory. Shows file names and sizes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path relative to workspace root (default: '.')"},
                "recursive": {"type": "boolean", "description": "List recursively (default: false)"},
                "pattern": {"type": "string", "description": "Glob pattern to filter (e.g. '*.py')"},
            },
        },
    },
    {
        "name": "search",
        "description": "Search for a pattern across files in the workspace. Returns matching lines with context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory or file to search in (default: '.')"},
                "include": {"type": "string", "description": "File glob to include (e.g. '*.py')"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "git_status",
        "description": "Show git status — modified, staged, and untracked files.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "git_diff",
        "description": "Show git diff. Can diff staged changes, specific files, or commits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "File, commit, or 'staged' (default: working tree)"},
            },
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git commit history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of entries (default: 10)"},
                "file": {"type": "string", "description": "History for a specific file"},
            },
        },
    },
    {
        "name": "git_commit",
        "description": "Stage files and commit. Requires confirmation for large changes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to stage (default: all)"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "find_definition",
        "description": "Find where a function, class, or variable is defined in the codebase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name to find"},
                "path": {"type": "string", "description": "Directory to search (default: '.')"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "batch_edit",
        "description": "Find and replace exact text in a file. Safer than full rewrites.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File to edit"},
                "old_text": {"type": "string", "description": "Exact text to find"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
]


# ── Tool Execution ──────────────────────────────────────────────

def _resolve_path(path: str) -> Path:
    """Resolve a path relative to workspace root, with safety checks."""
    resolved = Path(WORKSPACE_ROOT, path).resolve()
    workspace = Path(WORKSPACE_ROOT).resolve()
    if not str(resolved).startswith(str(workspace)):
        raise PermissionError(f"Access denied: {path} is outside workspace")
    return resolved


def tool_read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Read a file and return line-numbered content."""
    p = _resolve_path(path)
    if not p.exists():
        return f"Error: {path} does not exist"
    if not p.is_file():
        return f"Error: {path} is not a file"

    lines = p.read_text(errors="replace").splitlines()
    total = len(lines)

    if total > MAX_FILE_LINES and start_line is None:
        return (
            f"Warning: {path} has {total} lines. Showing first 100.\n"
            f"Use start_line/end_line to read specific sections.\n\n"
            + "\n".join(f"{i+1:4d} | {l}" for i, l in enumerate(lines[:100]))
        )

    s = (start_line or 1) - 1
    e = end_line or total
    selected = lines[s:e]

    return "\n".join(f"{s+i+1:4d} | {l}" for i, l in enumerate(selected))


def tool_write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories as needed."""
    p = _resolve_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    return f"Wrote {lines} lines to {path}"


def tool_edit_file(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Replace lines in an existing file."""
    p = _resolve_path(path)
    if not p.exists():
        return f"Error: {path} does not exist"

    lines = p.read_text().splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    if new_content and not new_content.endswith("\n"):
        new_lines[-1] += "\n"

    lines[start_line - 1 : end_line] = new_lines
    p.write_text("".join(lines))

    return f"Edited {path}: replaced lines {start_line}-{end_line} with {len(new_lines)} new lines"


def tool_run_command(command: str, timeout: int = None) -> str:
    """Execute a shell command."""
    timeout = timeout or SHELL_TIMEOUT
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=WORKSPACE_ROOT
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + f"STDERR: {result.stderr}"
        output += f"\n[exit code: {result.returncode}]"
        # Truncate very long outputs
        if len(output) > 10000:
            output = output[:5000] + "\n\n... (truncated) ...\n\n" + output[-3000:]
        return output.strip()
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def tool_list_files(path: str = ".", recursive: bool = False, pattern: str = None) -> str:
    """List files in a directory."""
    p = _resolve_path(path)
    if not p.exists():
        return f"Error: {path} does not exist"
    if not p.is_dir():
        return f"Error: {path} is not a directory"

    if recursive:
        glob_pattern = pattern or "*"
        entries = sorted(p.rglob(glob_pattern))
    else:
        entries = sorted(p.iterdir())
        if pattern:
            entries = [e for e in entries if e.match(pattern)]

    lines = []
    for entry in entries[:200]:  # cap at 200 entries
        rel = entry.relative_to(Path(WORKSPACE_ROOT).resolve())
        if entry.is_dir():
            lines.append(f"  {rel}/")
        else:
            size = entry.stat().st_size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size // 1024}KB"
            else:
                size_str = f"{size // (1024*1024)}MB"
            lines.append(f"  {rel} ({size_str})")

    header = f"{len(entries)} items in {path}"
    if len(entries) > 200:
        header += " (showing first 200)"
    return header + "\n" + "\n".join(lines)


def tool_search(pattern: str, path: str = ".", include: str = None) -> str:
    """Search for a regex pattern across files."""
    cmd = f"grep -rn"
    if include:
        cmd += f" --include='{include}'"
    cmd += f" -E '{pattern}' {path}"

    result = tool_run_command(cmd, timeout=15)
    lines = result.strip().split("\n")
    if len(lines) > 50:
        return "\n".join(lines[:50]) + f"\n\n... ({len(lines) - 50} more matches)"
    return result


def tool_git_status() -> str:
    """Show git status."""
    return tool_run_command("git status --short --branch")


def tool_git_diff(target: str = None) -> str:
    """Show git diff."""
    if target == "staged":
        return tool_run_command("git diff --cached")
    elif target:
        return tool_run_command(f"git diff {target}")
    return tool_run_command("git diff")


def tool_git_log(count: int = 10, file: str = None) -> str:
    """Show git log."""
    cmd = f"git log --oneline -n {count}"
    if file:
        cmd += f" -- {file}"
    return tool_run_command(cmd)


def tool_git_commit(message: str, files: list = None) -> str:
    """Stage and commit."""
    if files:
        for f in files:
            tool_run_command(f"git add {f}")
    else:
        tool_run_command("git add -A")
    return tool_run_command(f'git commit -m "{message}"')


def tool_find_definition(symbol: str, path: str = ".") -> str:
    """Find where a symbol is defined."""
    patterns = [
        f"def {symbol}",
        f"class {symbol}",
        f"{symbol}\\s*=",
    ]
    results = []
    for pat in patterns:
        out = tool_search(pat, path, include="*.py")
        if out and "Error" not in out:
            results.append(out)
    return "\n".join(results) if results else f"No definition found for '{symbol}'"


def tool_batch_edit(path: str, old_text: str, new_text: str) -> str:
    """Find and replace exact text in a file."""
    p = _resolve_path(path)
    if not p.exists():
        return f"Error: {path} does not exist"
    content = p.read_text()
    if old_text not in content:
        return f"Error: exact text not found in {path}"
    count = content.count(old_text)
    content = content.replace(old_text, new_text)
    p.write_text(content)
    return f"Replaced {count} occurrence(s) in {path}"



# ── Dispatcher ──────────────────────────────────────────────────

# Import extended tools
try:
    from tools_extended import EXTENDED_TOOLS, EXTENDED_SCHEMAS
    _has_extended = True
except ImportError:
    try:
        from projects.xtcode.tools_extended import EXTENDED_TOOLS, EXTENDED_SCHEMAS
        _has_extended = True
    except ImportError:
        _has_extended = False

# Import todo tools
try:
    from todo import tool_todo, TODO_SCHEMA
    _has_todo = True
except ImportError:
    try:
        from projects.xtcode.todo import tool_todo, TODO_SCHEMA
        _has_todo = True
    except ImportError:
        _has_todo = False

# Import memory tools
try:
    from memory import tool_memory, MEMORY_SCHEMA
    _has_memory = True
except ImportError:
    try:
        from projects.xtcode.memory import tool_memory, MEMORY_SCHEMA
        _has_memory = True
    except ImportError:
        _has_memory = False

TOOL_HANDLERS = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "run_command": tool_run_command,
    "list_files": tool_list_files,
    "search": tool_search,
}

# Merge extended tools
if _has_extended:
    TOOL_HANDLERS.update(EXTENDED_TOOLS)
def get_tool_schemas():
    """Return OpenAI-compatible tool schemas for all tools."""
    return [
        {"type": "function", "function": {"name": "read_file", "description": "Read a file and return its contents", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to read"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "write_file", "description": "Create or overwrite a file", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to write"}, "content": {"type": "string", "description": "Content to write"}}, "required": ["path", "content"]}}},
        {"type": "function", "function": {"name": "edit_file", "description": "Replace specific text in a file. Use old_text to find and new_text to replace.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}, "old_text": {"type": "string", "description": "Text to find"}, "new_text": {"type": "string", "description": "Replacement text"}}, "required": ["path", "old_text", "new_text"]}}},
        {"type": "function", "function": {"name": "run_command", "description": "Execute a shell command and return output", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Shell command to run"}}, "required": ["command"]}}},
        {"type": "function", "function": {"name": "list_files", "description": "List files and directories at a path", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory path to list (default: .)"}}, "required": []}}},
        {"type": "function", "function": {"name": "search", "description": "Search for a pattern in files using grep", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Search pattern (regex)"}, "path": {"type": "string", "description": "Directory to search in (default: .)"}, "include": {"type": "string", "description": "File glob pattern, e.g. '*.py'"}}, "required": ["pattern"]}}},
        {"type": "function", "function": {"name": "todo", "description": "Manage a todo/task list. Actions: list, add, complete, remove", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["list", "add", "complete", "remove"]}, "text": {"type": "string", "description": "Todo text (for add)"}, "index": {"type": "integer", "description": "Todo index (for complete/remove)"}}, "required": ["action"]}}},
        {"type": "function", "function": {"name": "memory", "description": "Project memory — remember context across sessions. Actions: get, set, list, delete", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["get", "set", "list", "delete"]}, "key": {"type": "string", "description": "Memory key"}, "value": {"type": "string", "description": "Memory value (for set)"}}, "required": ["action"]}}},
    ]

def execute_tool(name, arguments):
    """Execute a tool by name with given arguments."""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"Error: unknown tool '{name}'"
    try:
        return handler(**arguments)
    except Exception as e:
        return f"Error executing {name}: {e}"
