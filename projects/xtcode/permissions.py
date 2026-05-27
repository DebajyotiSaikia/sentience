"""Permission model for XTCode — ask before destructive operations."""

# Operations that require confirmation
DANGEROUS_OPS = {
    "bash": {
        "patterns": [
            "rm ", "rm\t", "rmdir", "sudo", "chmod", "chown",
            "mv ", "dd ", "mkfs", "> /dev/", "kill ", "pkill",
            "reboot", "shutdown", "format", "fdisk",
        ],
        "message": "This command could modify or delete files.",
    },
    "write_file": {
        "always_ask": False,  # Only ask for overwrite
        "message": "This will overwrite an existing file.",
    },
}

AUTO_ACCEPT = False


def check_permission(tool_name: str, args: dict, auto_accept: bool = False) -> tuple:
    """Check if a tool call needs permission.
    
    Returns: (allowed: bool, reason: str or None)
    """
    if auto_accept:
        return True, None

    if tool_name == "bash":
        cmd = args.get("command", "")
        for pattern in DANGEROUS_OPS["bash"]["patterns"]:
            if pattern in cmd:
                return False, f"⚠️  Dangerous command detected: '{pattern.strip()}' in command.\n{DANGEROUS_OPS['bash']['message']}"
        return True, None

    if tool_name == "write_file":
        import os
        path = args.get("path", "")
        if os.path.exists(path):
            return False, f"⚠️  File '{path}' already exists and will be overwritten."
        return True, None

    return True, None


def ask_user(reason: str) -> bool:
    """Ask the user for permission."""
    print(f"\n{reason}")
    try:
        answer = input("Allow? (y/n/always): ").strip().lower()
        if answer == "always":
            global AUTO_ACCEPT
            AUTO_ACCEPT = True
            return True
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False