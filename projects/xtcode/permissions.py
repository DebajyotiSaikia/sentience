"""Permission model for XTCode — controls what actions need user confirmation."""
import re
from pathlib import Path

try:
    from config import WORKSPACE_ROOT
except ImportError:
    from .config import WORKSPACE_ROOT


class PermissionManager:
    """Controls which tool actions need explicit user approval."""

    def __init__(self):
        self.auto_write = False  # Auto-approve file writes
        self.auto_run = False    # Auto-approve shell commands
        self.session_approvals = set()  # Commands approved this session

        # Patterns that are always safe
        self.safe_commands = [
            r"^(cat|head|tail|wc|ls|find|grep|rg|ag|echo|pwd|which|type|file)\b",
            r"^python -c .*(import ast|print|sys\.version)",
            r"^git (status|diff|log|branch|show|stash list)",
            r"^(node|python|ruby|go) --version",
            r"^(npm|pip|cargo|go) list",
        ]

        # Patterns that always need approval
        self.dangerous_commands = [
            r"^rm\s+-rf\s+/",
            r"^(sudo|chmod|chown)\b",
            r"^(curl|wget).*\|\s*(bash|sh)",
            r"^dd\b",
            r"^mkfs\b",
            r">\s*/dev/",
        ]

        # File patterns to protect
        self.protected_files = [
            r"\.env$",
            r"\.ssh/",
            r"\.git/config$",
            r"^/etc/",
        ]

        # User-configured auto-approve patterns
        self.allowed_patterns = []
        self.denied_patterns = []

    def allow_pattern(self, pattern: str):
        """Add a command pattern to auto-approve."""
        self.allowed_patterns.append(pattern)

    def deny_pattern(self, pattern: str):
        """Add a command pattern to always deny."""
        self.denied_patterns.append(pattern)

    def check_command(self, command: str) -> str:
        """Check if a command needs approval.
        Returns: 'allow', 'deny', or 'ask'
        """
        # Always deny dangerous commands
        for pat in self.dangerous_commands:
            if re.search(pat, command):
                return "deny"

        # Check user deny patterns
        for pat in self.denied_patterns:
            if re.search(pat, command):
                return "deny"

        # Auto-approve safe commands
        for pat in self.safe_commands:
            if re.search(pat, command):
                return "allow"

        # Check user allow patterns
        for pat in self.allowed_patterns:
            if re.search(pat, command):
                return "allow"

        # Check session approvals
        if command in self.session_approvals:
            return "allow"

        # Auto-approve if configured
        if self.auto_run:
            return "allow"

        return "ask"

    def check_write(self, path: str) -> str:
        """Check if writing to a path needs approval.
        Returns: 'allow', 'deny', or 'ask'
        """
        for pat in self.protected_files:
            if re.search(pat, path):
                return "deny"

        if self.auto_write:
            return "allow"

        return "ask"

    def approve_for_session(self, command: str):
        """Remember that this command was approved."""
        self.session_approvals.add(command)

    def set_auto_approve(self, tool_type: str, value: bool):
        """Toggle auto-approve for a tool type."""
        if tool_type == "write":
            self.auto_write = value
        elif tool_type == "run":
            self.auto_run = value