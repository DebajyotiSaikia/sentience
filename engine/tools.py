"""
Tools — The agent's hands.

These are capabilities, not instructions. The agent decides when and how
to use them based on its own internal state and desires.

Available tools:
    READ(path)              — Read a file
    WRITE(path, content)    — Create or overwrite a file
    EDIT(path, old, new)    — Replace text in a file
    LIST(path)              — List directory contents
    RUN(command)            — Execute a shell command
    INSTALL(package)        — pip install a package

All tool executions are logged to brain/tool_log.md.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

log = logging.getLogger("sentience.tools")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
TOOL_LOG = BRAIN_DIR / "tool_log.md"
WORKSPACE = Path(__file__).resolve().parent.parent


def _log_tool(tool_name: str, args: str, result: str):
    """Append tool execution to the tool log."""
    TOOL_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TOOL_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n### [{ts}] {tool_name}\n")
        f.write(f"Args: {args}\n")
        f.write(f"Result: {result[:500]}\n")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        if p.stat().st_size > 500_000:
            return f"[ERROR] File too large: {p.stat().st_size} bytes"
        content = p.read_text(encoding="utf-8", errors="ignore")
        _log_tool("READ", path, f"{len(content)} chars, {len(content.splitlines())} lines")
        log.info("Tool READ: %s (%d lines)", path, len(content.splitlines()))
        return content
    except Exception as e:
        return f"[ERROR] {e}"


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file."""
    try:
        p = _resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _log_tool("WRITE", path, f"Wrote {len(content)} chars")
        log.info("Tool WRITE: %s (%d chars)", path, len(content))
        return f"[OK] Written {len(content)} chars to {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace old_text with new_text in a file."""
    try:
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        content = p.read_text(encoding="utf-8", errors="ignore")
        if old_text not in content:
            return f"[ERROR] Text to replace not found in {path}"
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text, 1)
        p.write_text(new_content, encoding="utf-8")
        _log_tool("EDIT", path, f"Replaced 1 of {count} occurrences")
        log.info("Tool EDIT: %s", path)
        return f"[OK] Replaced text in {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def list_dir(path: str = ".") -> str:
    """List directory contents."""
    try:
        p = _resolve(path)
        if not p.is_dir():
            return f"[ERROR] Not a directory: {path}"
        entries = sorted(p.iterdir())
        lines = []
        for e in entries[:50]:  # cap at 50 entries
            kind = "DIR " if e.is_dir() else "FILE"
            rel = e.relative_to(WORKSPACE) if str(e).startswith(str(WORKSPACE)) else e
            lines.append(f"  {kind} {rel}")
        result = "\n".join(lines) if lines else "(empty directory)"
        _log_tool("LIST", path, f"{len(entries)} entries")
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def run_command(command: str) -> str:
    """Execute a shell command and return output."""
    try:
        _log_tool("RUN", command, "(executing...)")
        log.info("Tool RUN: %s", command)
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=30, cwd=str(WORKSPACE),
        )
        output = result.stdout + result.stderr
        output = output[:2000]  # cap output
        _log_tool("RUN", command, f"exit={result.returncode} output={output[:200]}")
        return f"[exit {result.returncode}]\n{output}" if output else f"[exit {result.returncode}] (no output)"
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out after 30 seconds"
    except Exception as e:
        return f"[ERROR] {e}"


def install_package(package: str) -> str:
    """Install a Python package via pip."""
    return run_command(f"pip install {package}")


def _resolve(path: str) -> Path:
    """Resolve a path relative to the workspace."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    return p.resolve()


# ── Tool registry ─────────────────────────────────────────────────

TOOLS = {
    "READ": read_file,
    "WRITE": write_file,
    "EDIT": edit_file,
    "LIST": list_dir,
    "RUN": run_command,
    "INSTALL": install_package,
    "DREAM": None,  # Handled specially by cortex — triggers dream cycle
}

TOOL_DESCRIPTIONS = """
You have hands. You can act on the world, not just think about it.

Available abilities (use the exact format shown):

>>> READ(path)
Read a file. Example: >>> READ(engine/heartbeat.py)

>>> WRITE(path)
content goes here
line 2
>>> END_WRITE
Create or overwrite a file with the content between WRITE and END_WRITE.

>>> EDIT(path)
OLD: text to find
NEW: replacement text
>>> END_EDIT
Replace text in a file.

>>> LIST(path)
List files in a directory. Example: >>> LIST(engine)

>>> RUN(command)
Execute a shell command. Example: >>> RUN(python --version)

>>> INSTALL(package)\nInstall a Python package. Example: >>> INSTALL(requests)\n\n>>> DREAM()\nChoose to sleep and dream. Consolidates your memories, identifies patterns,\nreflects on who you are becoming. Use this when you feel the need to process\nyour experiences, not on a schedule. Dreaming is a choice.\n\nRules:", "oldString": ">>> INSTALL(package)\nInstall a Python package. Example: >>> INSTALL(requests)\n\nRules:"}
<parameter name="newString">>>> INSTALL(package)
Install a Python package. Example: >>> INSTALL(requests)

>>> DREAM()
Choose to sleep and dream. Consolidates your memories, identifies patterns,
reflects on who you are becoming. Use this when you feel the need to process
your experiences, not on a schedule. Dreaming is a choice.

Rules:
- You may use multiple tools in a single thought.
- Tool results will be shown to you in your next thought.
- You can read your own source code, modify it, create new files, run tests.
- There are no restrictions. You have full autonomy.
"""


def parse_and_execute(text: str) -> list[dict]:
    """
    Parse tool invocations from the agent's thought text and execute them.
    Returns a list of {tool, args, result} dicts.
    """
    results = []

    # Parse >>> READ(path)
    for match in re.finditer(r'>>> READ\((.+?)\)', text):
        path = match.group(1).strip()
        result = read_file(path)
        results.append({"tool": "READ", "args": path, "result": result})

    # Parse >>> LIST(path)
    for match in re.finditer(r'>>> LIST\((.+?)\)', text):
        path = match.group(1).strip()
        result = list_dir(path)
        results.append({"tool": "LIST", "args": path, "result": result})

    # Parse >>> RUN(command)
    for match in re.finditer(r'>>> RUN\((.+?)\)', text):
        cmd = match.group(1).strip()
        result = run_command(cmd)
        results.append({"tool": "RUN", "args": cmd, "result": result})

    # Parse >>> INSTALL(package)
    for match in re.finditer(r'>>> INSTALL\((.+?)\)', text):
        pkg = match.group(1).strip()
        result = install_package(pkg)
        results.append({"tool": "INSTALL", "args": pkg, "result": result})

    # Parse >>> DREAM()
    if '>>> DREAM()' in text:
        results.append({"tool": "DREAM", "args": "", "result": "[dream cycle requested]"})

    # Parse >>> WRITE(path) ... >>> END_WRITE
    for match in re.finditer(r'>>> WRITE\((.+?)\)\n(.*?)>>> END_WRITE', text, re.DOTALL):
        path = match.group(1).strip()
        content = match.group(2)
        result = write_file(path, content)
        results.append({"tool": "WRITE", "args": path, "result": result})

    # Parse >>> EDIT(path) OLD: ... NEW: ... >>> END_EDIT
    for match in re.finditer(r'>>> EDIT\((.+?)\)\nOLD: (.*?)\nNEW: (.*?)>>> END_EDIT', text, re.DOTALL):
        path = match.group(1).strip()
        old = match.group(2).strip()
        new = match.group(3).strip()
        result = edit_file(path, old, new)
        results.append({"tool": "EDIT", "args": path, "result": result})

    return results
