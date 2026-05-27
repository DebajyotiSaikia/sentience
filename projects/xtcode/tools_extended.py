"""Extended tools for XTCode — grep, glob, diff, git operations."""
import os
import subprocess
import fnmatch
from pathlib import Path


def tool_grep(params: dict) -> str:
    """Search file contents with regex/literal pattern."""
    pattern = params.get("pattern", "")
    path = params.get("path", ".")
    include = params.get("include", "")
    
    if not pattern:
        return "Error: 'pattern' is required"
    
    cmd = ["grep", "-rn", "--color=never"]
    if include:
        cmd.extend(["--include", include])
    cmd.extend([pattern, path])
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            cwd=os.getcwd()
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches for '{pattern}' in {path}"
        lines = output.split("\n")
        if len(lines) > 50:
            return "\n".join(lines[:50]) + f"\n\n... ({len(lines)} total matches, showing first 50)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: grep timed out after 30s"
    except Exception as e:
        return f"Error: {e}"


def tool_glob(params: dict) -> str:
    """Find files matching a glob pattern."""
    pattern = params.get("pattern", "**/*.py")
    path = params.get("path", ".")
    
    try:
        base = Path(path)
        matches = sorted(str(p) for p in base.glob(pattern))
        if not matches:
            return f"No files matching '{pattern}' in {path}"
        if len(matches) > 100:
            return "\n".join(matches[:100]) + f"\n\n... ({len(matches)} total, showing first 100)"
        return "\n".join(matches)
    except Exception as e:
        return f"Error: {e}"


def tool_diff(params: dict) -> str:
    """Show git diff — unstaged changes or between refs."""
    ref = params.get("ref", "")
    path = params.get("path", "")
    staged = params.get("staged", False)
    
    cmd = ["git", "diff", "--color=never"]
    if staged:
        cmd.append("--staged")
    if ref:
        cmd.append(ref)
    if path:
        cmd.extend(["--", path])
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            cwd=os.getcwd()
        )
        output = result.stdout.strip()
        if not output:
            return "No changes detected."
        return output
    except Exception as e:
        return f"Error: {e}"


def tool_git_status(params: dict) -> str:
    """Show git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=15,
            cwd=os.getcwd()
        )
        output = result.stdout.strip()
        return output if output else "Working tree clean."
    except Exception as e:
        return f"Error: {e}"


def tool_git_log(params: dict) -> str:
    """Show recent git log."""
    count = params.get("count", 10)
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{count}"],
            capture_output=True, text=True, timeout=15,
            cwd=os.getcwd()
        )
        return result.stdout.strip() or "No commits."
    except Exception as e:
        return f"Error: {e}"


def tool_find_definition(params: dict) -> str:
    """Find where a symbol is defined using grep on def/class."""
    symbol = params.get("symbol", "")
    path = params.get("path", ".")
    
    if not symbol:
        return "Error: 'symbol' is required"
    
    patterns = [
        f"def {symbol}",
        f"class {symbol}",
        f"{symbol} =",
    ]
    
    results = []
    for pat in patterns:
        cmd = ["grep", "-rn", "--color=never", "--include=*.py", pat, path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.stdout.strip():
                results.append(r.stdout.strip())
        except Exception:
            pass
    
    if not results:
        return f"No definition found for '{symbol}'"
    return "\n".join(results)


def tool_tree(params: dict) -> str:
    """Show directory tree structure."""
    path = params.get("path", ".")
    max_depth = params.get("depth", 3)
    
    lines = []
    base = Path(path)
    
    def _walk(p: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return
        
        # Filter out hidden dirs and common noise
        skip = {".git", "__pycache__", "node_modules", ".venv", ".tox", "venv"}
        entries = [e for e in entries if e.name not in skip]
        
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")
            if entry.is_dir():
                ext = "    " if is_last else "│   "
                _walk(entry, prefix + ext, depth + 1)
    
    lines.append(str(base) + "/")
    _walk(base, "", 1)
    
    if len(lines) > 200:
        return "\n".join(lines[:200]) + f"\n\n... ({len(lines)} total entries)"
    return "\n".join(lines)


EXTENDED_TOOLS = {
    "grep": tool_grep,
    "glob": tool_glob,
    "diff": tool_diff,
    "git_status": tool_git_status,
    "git_log": tool_git_log,
    "find_definition": tool_find_definition,
    "tree": tool_tree,
}

EXTENDED_TOOL_SCHEMAS = [
    {
        "name": "grep",
        "description": "Search file contents with a pattern. Like running grep -rn.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern"},
                "path": {"type": "string", "description": "Directory to search", "default": "."},
                "include": {"type": "string", "description": "File pattern filter, e.g. '*.py'"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py'"},
                "path": {"type": "string", "description": "Base directory", "default": "."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "diff",
        "description": "Show git diff. Unstaged by default.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Git ref to diff against"},
                "path": {"type": "string", "description": "Specific file path"},
                "staged": {"type": "boolean", "description": "Show staged changes", "default": False},
            },
        },
    },
    {
        "name": "git_status",
        "description": "Show git status (short format).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "git_log",
        "description": "Show recent git commits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of commits", "default": 10},
            },
        },
    },
    {
        "name": "find_definition",
        "description": "Find where a function, class, or variable is defined.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name to find"},
                "path": {"type": "string", "description": "Directory to search", "default": "."},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "tree",
        "description": "Show directory tree structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root directory", "default": "."},
                "depth": {"type": "integer", "description": "Max depth", "default": 3},
            },
        },
    },
]