"""XTCode terminal UI — colors, formatting, spinners."""
import sys
import os
import threading
import time
import shutil

# ─── Color codes ───
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

# Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
GRAY = "\033[90m"

# Backgrounds
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"

# Check if colors are supported
NO_COLOR = os.environ.get("NO_COLOR") or not sys.stdout.isatty()

def _c(color: str, text: str) -> str:
    if NO_COLOR:
        return text
    return f"{color}{text}{RESET}"

def bold(text: str) -> str:
    return _c(BOLD, text)

def dim(text: str) -> str:
    return _c(DIM, text)

def red(text: str) -> str:
    return _c(RED, text)

def green(text: str) -> str:
    return _c(GREEN, text)

def yellow(text: str) -> str:
    return _c(YELLOW, text)

def blue(text: str) -> str:
    return _c(BLUE, text)

def magenta(text: str) -> str:
    return _c(MAGENTA, text)

def cyan(text: str) -> str:
    return _c(CYAN, text)

def gray(text: str) -> str:
    return _c(GRAY, text)


def get_terminal_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def hr(char: str = "─", color=GRAY) -> str:
    w = get_terminal_width()
    line = char * w
    return _c(color, line)


def banner():
    """Print the XTCode startup banner."""
    w = get_terminal_width()
    print()
    print(_c(BOLD + CYAN, "  ╔═╗╔╦╗╔═╗╔═╗╔╦╗╔═╗"))
    print(_c(BOLD + CYAN, "  ╠╣  ║ ║  ║ ║ ║║║╣ "))
    print(_c(BOLD + CYAN, "  ╩   ╩ ╚═╝╚═╝═╩╝╚═╝"))
    print()
    print(f"  {dim('Autonomous coding agent')}")
    print(f"  {dim('Type')} {bold('/help')} {dim('for commands')}")
    print(hr())
    print()


def tool_header(name: str, args: dict) -> str:
    """Format a tool execution header."""
    icon = {
        "read_file": "📄",
        "write_file": "✏️",
        "edit_file": "🔧",
        "run_command": "⚡",
        "list_files": "📁",
        "search": "🔍",
        "git_status": "📊",
        "git_diff": "📝",
        "git_log": "📜",
        "git_commit": "💾",
    }.get(name, "🔨")

    # Format args concisely
    if name == "read_file":
        detail = args.get("path", "")
    elif name == "write_file":
        detail = args.get("path", "")
    elif name == "edit_file":
        path = args.get("path", "")
        start = args.get("start_line", "?")
        end = args.get("end_line", "?")
        detail = f"{path}:{start}-{end}"
    elif name == "run_command":
        cmd = args.get("command", "")
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
        detail = cmd
    elif name == "search":
        detail = args.get("pattern", "")
    elif name == "list_files":
        detail = args.get("path", ".")
    elif name in ("git_status", "git_diff", "git_log"):
        detail = ""
    elif name == "git_commit":
        detail = args.get("message", "")[:50]
    else:
        detail = str(args)[:60]

    return f"{icon} {_c(BOLD + YELLOW, name)} {_c(DIM, detail)}"


def tool_result_summary(name: str, result: str, max_lines: int = 20) -> str:
    """Format tool result — truncate if needed."""
    lines = result.split("\n")
    if len(lines) <= max_lines:
        return _c(DIM, result)
    
    shown = lines[:max_lines]
    hidden = len(lines) - max_lines
    return _c(DIM, "\n".join(shown)) + f"\n{_c(GRAY, f'  ... ({hidden} more lines)')}"


def user_prompt() -> str:
    """The input prompt string."""
    return _c(BOLD + GREEN, "❯ ")


def assistant_prefix() -> str:
    """Prefix before assistant text."""
    return _c(BOLD + BLUE, "┃ ")


def format_assistant_text(text: str) -> str:
    """Format assistant response text."""
    if not text.strip():
        return ""
    lines = text.split("\n")
    prefix = _c(BLUE, "│ ") if not NO_COLOR else "  "
    return "\n".join(f"{prefix}{line}" for line in lines)


def error_msg(text: str) -> str:
    return _c(BOLD + RED, f"✗ {text}")


def success_msg(text: str) -> str:
    return _c(BOLD + GREEN, f"✓ {text}")


def info_msg(text: str) -> str:
    return _c(CYAN, f"ℹ {text}")


def warning_msg(text: str) -> str:
    return _c(YELLOW, f"⚠ {text}")


def cost_display(input_tokens: int, output_tokens: int, cost: float, duration: float) -> str:
    """Format cost/token info."""
    return _c(DIM, f"  tokens: {input_tokens:,} in / {output_tokens:,} out · ${cost:.4f} · {duration:.1f}s")


def files_changed_display(files: list) -> str:
    """Show what files were modified."""
    if not files:
        return ""
    parts = [_c(DIM, "  files changed: ")]
    parts.append(_c(YELLOW, ", ".join(files)))
    return "".join(parts)


class Spinner:
    """A simple terminal spinner for long operations."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "Thinking"):
        self.message = message
        self._running = False
        self._thread = None
    
    def start(self):
        if not sys.stdout.isatty():
            return
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def _spin(self):
        i = 0
        while self._running:
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(f"\r{_c(CYAN, frame)} {_c(DIM, self.message)}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)
    
    def stop(self, clear: bool = True):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        if clear and sys.stdout.isatty():
            sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
            sys.stdout.flush()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()