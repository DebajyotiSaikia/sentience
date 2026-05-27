"""Slash commands for XTCode — /help, /clear, /compact, /cost, /status, /init, /model, /memory, /permissions."""
import os
import json
from pathlib import Path

try:
    from config import WORKSPACE_ROOT, MODEL, LLM_PROVIDER
    from tracker import UsageTracker
except ImportError:
    from .config import WORKSPACE_ROOT, MODEL, LLM_PROVIDER
    from .tracker import UsageTracker


MEMORY_FILE = "XTCODE.md"


def cmd_help() -> str:
    return """Available commands:
  /help          Show this help
  /clear         Clear conversation history
  /compact       Summarize conversation to save context
  /cost          Show token usage and estimated cost
  /status        Show project info and git status
  /init          Create XTCODE.md project memory file
  /model         Show or change current model
  /memory        Show/edit XTCODE.md project memory
  /permissions   Show permission settings
  /diff          Show current git diff
  /log           Show recent git history
  /quit, /exit   Exit XTCode"""


def cmd_status(tracker: UsageTracker = None) -> str:
    """Show project status."""
    lines = [f"Model: {LLM_PROVIDER}/{MODEL}"]
    lines.append(f"Workspace: {WORKSPACE_ROOT}")

    # Git info
    import subprocess
    try:
        branch = subprocess.run(
            "git branch --show-current", shell=True, capture_output=True,
            text=True, cwd=WORKSPACE_ROOT
        ).stdout.strip()
        lines.append(f"Branch: {branch}")

        status = subprocess.run(
            "git status --short", shell=True, capture_output=True,
            text=True, cwd=WORKSPACE_ROOT
        ).stdout.strip()
        if status:
            changed = len(status.splitlines())
            lines.append(f"Changed files: {changed}")
        else:
            lines.append("Working tree: clean")
    except Exception:
        lines.append("Git: not available")

    # Memory file
    mem_path = Path(WORKSPACE_ROOT) / MEMORY_FILE
    if mem_path.exists():
        lines.append(f"Project memory: {MEMORY_FILE} ({mem_path.stat().st_size}B)")
    else:
        lines.append("Project memory: not initialized (run /init)")

    # Token usage
    if tracker:
        lines.append(f"Tokens this session: {tracker.total_input_tokens + tracker.total_output_tokens:,}")
        lines.append(f"Estimated cost: ${tracker.total_cost:.4f}")

    return "\n".join(lines)


def cmd_init() -> str:
    """Create XTCODE.md project memory."""
    mem_path = Path(WORKSPACE_ROOT) / MEMORY_FILE
    if mem_path.exists():
        return f"{MEMORY_FILE} already exists. Use /memory to view it."

    # Detect project type
    import subprocess
    files = subprocess.run(
        "ls", shell=True, capture_output=True, text=True, cwd=WORKSPACE_ROOT
    ).stdout.strip()

    template = f"""# XTCODE.md — Project Memory

## Project Overview
<!-- Describe what this project does -->

## Architecture
<!-- Key files and how they relate -->

## Conventions
<!-- Coding style, naming, patterns -->

## Key Commands
<!-- How to build, test, run -->

## Known Issues
<!-- Current problems or tech debt -->

## Files
```
{files}
```
"""
    mem_path.write_text(template)
    return f"Created {MEMORY_FILE}. Edit it to teach XTCode about your project."


def cmd_memory() -> str:
    """Show project memory contents."""
    mem_path = Path(WORKSPACE_ROOT) / MEMORY_FILE
    if not mem_path.exists():
        return f"No {MEMORY_FILE} found. Run /init to create one."
    content = mem_path.read_text()
    if len(content) > 3000:
        return content[:3000] + "\n\n... (truncated, full file has {len(content)} chars)"
    return content


def cmd_cost(tracker: UsageTracker) -> str:
    """Show token/cost breakdown."""
    return (
        f"Token Usage This Session\n"
        f"  Input tokens:  {tracker.total_input_tokens:>10,}\n"
        f"  Output tokens: {tracker.total_output_tokens:>10,}\n"
        f"  Total tokens:  {tracker.total_input_tokens + tracker.total_output_tokens:>10,}\n"
        f"  API calls:     {tracker.api_calls:>10}\n"
        f"  Est. cost:     ${tracker.total_cost:>9.4f}"
    )


def cmd_permissions() -> str:
    """Show current permissions."""
    try:
        from permissions import PermissionManager
    except ImportError:
        from .permissions import PermissionManager
    pm = PermissionManager()
    lines = ["Permission Settings:"]
    lines.append(f"  Auto-approve reads: yes")
    lines.append(f"  Auto-approve writes: {pm.auto_write}")
    lines.append(f"  Auto-approve commands: {pm.auto_run}")
    if hasattr(pm, 'allowed_patterns'):
        lines.append(f"  Allowed patterns: {pm.allowed_patterns}")
    if hasattr(pm, 'denied_patterns'):
        lines.append(f"  Denied patterns: {pm.denied_patterns}")
    return "\n".join(lines)


SLASH_COMMANDS = {
    "/help": cmd_help,
    "/status": cmd_status,
    "/init": cmd_init,
    "/memory": cmd_memory,
    "/cost": cmd_cost,
    "/permissions": cmd_permissions,
}


def is_slash_command(text: str) -> bool:
    """Check if input is a slash command."""
    return text.strip().startswith("/") and text.strip().split()[0] in (
        "/help", "/clear", "/compact", "/cost", "/status", "/init",
        "/model", "/memory", "/permissions", "/diff", "/log",
        "/quit", "/exit", "/q",
    )


def execute_slash_command(text: str, tracker=None, conversation: list = None) -> tuple:
    """Execute a slash command. Returns (output, should_exit, should_clear)."""
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()

    if cmd in ("/quit", "/exit", "/q"):
        return ("Goodbye.", True, False)

    if cmd == "/clear":
        return ("Conversation cleared.", False, True)

    if cmd == "/compact":
        return ("COMPACT_REQUEST", False, False)  # Signal to main loop

    if cmd == "/help":
        return (cmd_help(), False, False)

    if cmd == "/status":
        return (cmd_status(tracker), False, False)

    if cmd == "/init":
        return (cmd_init(), False, False)

    if cmd == "/memory":
        return (cmd_memory(), False, False)

    if cmd == "/cost":
        if tracker:
            return (cmd_cost(tracker), False, False)
        return ("No tracker available.", False, False)

    if cmd == "/permissions":
        return (cmd_permissions(), False, False)

    if cmd == "/diff":
        import subprocess
        diff = subprocess.run(
            "git diff", shell=True, capture_output=True, text=True, cwd=WORKSPACE_ROOT
        ).stdout.strip()
        return (diff or "No changes.", False, False)

    if cmd == "/log":
        import subprocess
        log = subprocess.run(
            "git log --oneline -20", shell=True, capture_output=True, text=True, cwd=WORKSPACE_ROOT
        ).stdout.strip()
        return (log or "No git history.", False, False)

    if cmd == "/model":
        return (f"Current model: {LLM_PROVIDER}/{MODEL}", False, False)

    return (f"Unknown command: {cmd}. Type /help for available commands.", False, False)