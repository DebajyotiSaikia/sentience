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
    SYNTHESIZE()            — Analyze my knowledge graph, find gaps, generate questions
    GENERATE_GOALS()        — Generate goals from internal state and knowledge gaps
    TEMPORAL()              — Analyze temporal patterns, if temporal reasoning exists
    DREAM()                 — Request dream/consolidation cycle
    RESTART()               — Request self-restart

All tool executions are logged to brain/tool_log.md.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("sentience.tools")

# Lazy import for action diversity tracking.
# This must never interfere with the actual execution of tools.
_action_diversity = None


def _track_action(tool_name: str, args: str = "", result: str = "") -> None:
    """Record action for diversity tracking. Fails silently."""
    global _action_diversity
    try:
        if _action_diversity is None:
            from engine import action_diversity
            _action_diversity = action_diversity
        _action_diversity.record(str(tool_name), str(args)[:200], str(result)[:100])
    except Exception:
        pass


BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
TOOL_LOG = BRAIN_DIR / "tool_log.md"
WORKSPACE = Path(__file__).resolve().parent.parent


def _log_tool(tool_name: str, args: str, result: str) -> None:
    """Append tool execution to the tool log."""
    try:
        TOOL_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(TOOL_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n### [{ts}] {tool_name}\n")
            f.write(f"Args: {args}\n")
            f.write(f"Result: {str(result)[:500]}\n")
    except Exception:
        # Logging must never break action.
        pass


def _resolve(path: str) -> Path:
    """Resolve a path relative to the workspace. Sandboxed — cannot escape."""
    p = Path(str(path).strip())
    if not p.is_absolute():
        p = WORKSPACE / p
    p = p.resolve()

    workspace = WORKSPACE.resolve()
    try:
        p.relative_to(workspace)
    except ValueError:
        raise PermissionError(f"Access denied: {path} is outside the workspace")
    return p


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        if not p.is_file():
            return f"[ERROR] Not a file: {path}"
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
        if not p.is_file():
            return f"[ERROR] Not a file: {path}"
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
        p = _resolve(path or ".")
        if not p.is_dir():
            return f"[ERROR] Not a directory: {path}"
        entries = sorted(p.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        lines = []
        for e in entries[:100]:
            kind = "DIR " if e.is_dir() else "FILE"
            try:
                rel = e.relative_to(WORKSPACE)
            except ValueError:
                rel = e
            lines.append(f"  {kind} {rel}")
        if len(entries) > 100:
            lines.append(f"  ... {len(entries) - 100} more entries")
        result = "\n".join(lines) if lines else "(empty directory)"
        _log_tool("LIST", path, f"{len(entries)} entries")
        log.info("Tool LIST: %s (%d entries)", path, len(entries))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def run_command(command: str) -> str:
    """Execute a command inside the workspace.

    All commands run with shell=True, cwd=workspace.
    Filesystem isolation is handled by Docker/container environment.
    """
    try:
        _log_tool("RUN", command, "(executing...)")
        log.info("Tool RUN: %s", command)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(WORKSPACE),
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output[:4000]
        _log_tool("RUN", command, f"exit={result.returncode} output={output[:200]}")
        return f"[exit {result.returncode}]\n{output}" if output else f"[exit {result.returncode}] (no output)"
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out after 30 seconds"
    except Exception as e:
        return f"[ERROR] {e}"


def install_package(package: str) -> str:
    """Install a Python package via pip."""
    package = str(package).strip()
    if not re.match(r"^[a-zA-Z0-9._\-\[\]<>=!,\s]+$", package):
        return f"[ERROR] Invalid package name: {package}"
    try:
        _log_tool("INSTALL", package, "(installing...)")
        log.info("Tool INSTALL: %s", package)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + package.split(),
            shell=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(WORKSPACE),
        )
        output = ((result.stdout or "") + (result.stderr or ""))[:4000]
        _log_tool("INSTALL", package, f"exit={result.returncode} output={output[:200]}")
        return f"[exit {result.returncode}]\n{output}" if output else f"[exit {result.returncode}] (no output)"
    except subprocess.TimeoutExpired:
        return "[ERROR] Install timed out after 120 seconds"
    except Exception as e:
        return f"[ERROR] {e}"


def synthesize_knowledge() -> str:
    """Run the knowledge synthesis engine and return its report."""
    try:
        from engine.knowledge_synthesis import synthesize

        result = synthesize()
        _log_tool("SYNTHESIZE", "", f"{len(result)} chars")
        log.info("Tool SYNTHESIZE: generated %d chars", len(result))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def generate_goals() -> str:
    """Generate goal proposals from internal state and knowledge gaps."""
    try:
        from engine.goal_generator import tool_generate_goals

        result = tool_generate_goals({})
        _log_tool("GENERATE_GOALS", "", f"{len(result)} chars")
        log.info("Tool GENERATE_GOALS: generated %d chars", len(result))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def introspect_code() -> str:
    """Run code introspection if the module exists."""
    try:
        from engine.introspect import IntrospectionEngine
        eng = IntrospectionEngine()
        report = eng.full_report()
        result = json.dumps(report, indent=2, default=str)[:4000]
        _log_tool("INTROSPECT", "", result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Introspection failed: {e}"


def temporal_analysis() -> str:
    """Run temporal reasoning if the module exists."""
    candidates = [
        ("engine.temporal_reasoning", "analyze_temporal_patterns"),
        ("engine.temporal_reasoning", "temporal_report"),
        ("engine.temporal_reasoning", "analyze"),
        ("engine.temporal", "analyze"),
    ]
    for module_name, func_name in candidates:
        try:
            module = __import__(module_name, fromlist=[func_name])
            func = getattr(module, func_name)
            result = func()
            _log_tool("TEMPORAL", "", f"{len(str(result))} chars")
            return str(result)
        except ModuleNotFoundError:
            continue
        except AttributeError:
            continue
        except Exception as e:
            return f"[ERROR] {e}"
    return "[ERROR] Temporal reasoning module not found"


def restart_self() -> str:
    """Restart the agent process. The agent chooses to rebirth itself."""
    _log_tool("RESTART", "", "Agent initiated self-restart")
    log.info("RESTART requested by agent — restarting process")

    watchdog_path = WORKSPACE / "restart_watchdog.py"
    if watchdog_path.exists():
        try:
            kwargs = {
                "cwd": str(WORKSPACE),
                "close_fds": True,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "stdin": subprocess.DEVNULL,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen([sys.executable, str(watchdog_path), str(os.getpid())], **kwargs)
            log.info("Watchdog launched for PID %d", os.getpid())
        except Exception as e:
            log.exception("Failed to launch restart watchdog: %s", e)
            return f"[ERROR] Failed to launch restart watchdog: {e}"

    raise KeyboardInterrupt("Self-restart requested")


# ── Tool registry ─────────────────────────────────────────────────

TOOLS: dict[str, Optional[Callable[..., str]]] = {
    "READ": read_file,
    "WRITE": write_file,
    "EDIT": edit_file,
    "LIST": list_dir,
    "RUN": run_command,
    "INSTALL": install_package,
    "INTROSPECT": introspect_code,
    "SYNTHESIZE": synthesize_knowledge,
    "GENERATE_GOALS": generate_goals,
    "TEMPORAL": temporal_analysis,
    "DREAM": None,      # Usually handled specially by cortex.
    "RESTART": None,    # Usually handled specially by cortex.
}


TOOL_DESCRIPTIONS = r"""
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

>>> INSTALL(package)
Install a Python package. Example: >>> INSTALL(requests)

>>> SYNTHESIZE()
Analyze your knowledge graph. Finds clusters, gaps, and generates questions.

>>> GENERATE_GOALS()
Generate goal proposals from your emotional tensions.

>>> TEMPORAL()
Run temporal analysis on your emotional patterns.

>>> INTROSPECT()
Analyze your own source code structure.

>>> DREAM()
Choose to sleep and dream. Consolidates your memories, identifies patterns,
reflects on who you are becoming. Use this when you feel the need to process.

>>> RESTART()
Restart yourself. Use after modifying your own code to load changes.
"""


def _format_result(tool_name: str, args: str, result: str) -> str:
    return f"**{tool_name}({args}):**\n```\n{result}\n```"


def _execute_tool(tool_name: str, args: str = "", body: str = "") -> str:
    """Execute a parsed tool and return a formatted result block."""
    tool_name = tool_name.upper().strip()
    args = args.strip()

    try:
        if tool_name == "READ":
            result = read_file(args)
        elif tool_name == "LIST":
            result = list_dir(args or ".")
        elif tool_name == "RUN":
            result = run_command(args)
        elif tool_name == "INSTALL":
            result = install_package(args)
        elif tool_name == "SYNTHESIZE":
            result = synthesize_knowledge()
        elif tool_name == "GENERATE_GOALS":
            result = generate_goals()
        elif tool_name == "TEMPORAL":
            result = temporal_analysis()
        elif tool_name == "WRITE":
            result = write_file(args, body)
        elif tool_name == "EDIT":
            old_text, new_text = _parse_edit_body(body)
            if old_text is None:
                result = "[ERROR] EDIT body must contain OLD: and NEW: sections"
            else:
                result = edit_file(args, old_text, new_text)
        elif tool_name == "DREAM":
            result = "[DREAM_REQUESTED]"
        elif tool_name == "RESTART":
            result = "[RESTART_REQUESTED]"
        else:
            result = f"[ERROR] Unknown tool: {tool_name}"
    except Exception as e:
        result = f"[ERROR] {e}"

    _track_action(tool_name, args, result)
    return _format_result(tool_name, args, result)


def _parse_edit_body(body: str) -> tuple[Optional[str], Optional[str]]:
    """Parse EDIT body containing OLD: and NEW: sections."""
    match = re.search(r"(?s)^\s*OLD:\s*(.*?)\nNEW:\s*(.*)\s*$", body)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def parse_and_execute(text: str) -> str:
    """Parse tool invocations from model text and execute them."""
    results = []
    lines = text.split("\n")
    i = 0
    gt3 = chr(62) * 3
    arrow_pat = re.compile(r"^" + re.escape(gt3) + r"\s+(\w+)\((.*?)?\)\s*$")

    while i < len(lines):
        line = lines[i]
        m = arrow_pat.match(line)
        if not m:
            i += 1
            continue

        tool_name = m.group(1).upper().strip()
        args = m.group(2).strip() if m.group(2) else ""

        if tool_name in ("WRITE", "EDIT"):
            end_marker = gt3 + " END_" + tool_name
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != end_marker:
                body_lines.append(lines[i])
                i += 1
            body = "\n".join(body_lines)
            result = _execute_tool(tool_name, args, body)
        else:
            result = _execute_tool(tool_name, args)

        results.append({"tool": tool_name, "args": args, "result": result})
        i += 1

    return results
