"""XTCode project memory — equivalent to CLAUDE.md.

Reads XTCODE.md from the project root to get persistent instructions,
conventions, and context that persists across sessions.
"""
import os

MEMORY_FILE = "XTCODE.md"

def load_project_memory(project_dir: str = ".") -> str:
    """Load XTCODE.md from project root if it exists."""
    path = os.path.join(project_dir, MEMORY_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    # Also check parent dirs up to 3 levels
    current = os.path.abspath(project_dir)
    for _ in range(3):
        parent = os.path.dirname(current)
        if parent == current:
            break
        path = os.path.join(parent, MEMORY_FILE)
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        current = parent
    return ""

def init_project_memory(project_dir: str = ".") -> str:
    """Create a default XTCODE.md in the project root."""
    path = os.path.join(project_dir, MEMORY_FILE)
    if os.path.exists(path):
        return f"XTCODE.md already exists at {path}"
    
    # Scan project to generate smart defaults
    files = []
    for root, dirs, fnames in os.walk(project_dir):
        # Skip hidden dirs, node_modules, venv, __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                   ('node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build')]
        for fname in fnames:
            rel = os.path.relpath(os.path.join(root, fname), project_dir)
            files.append(rel)
    
    # Detect project type
    has_package_json = "package.json" in files
    has_pyproject = "pyproject.toml" in files or "setup.py" in files
    has_cargo = "Cargo.toml" in files
    has_go = "go.mod" in files
    
    lang = "Python" if has_pyproject else "JavaScript/TypeScript" if has_package_json else "Rust" if has_cargo else "Go" if has_go else "Unknown"
    
    content = f"""# XTCODE.md — Project Memory

## Project
- Language: {lang}
- Files: {len(files)}

## Conventions
- (Add your coding conventions here)

## Architecture
- (Describe key modules and their relationships)

## Commands
- (Add common commands: test, build, lint, deploy)

## Notes
- (Anything XTCode should know when working on this project)
"""
    with open(path, "w") as f:
        f.write(content)
    return f"Created {path} — edit it to teach XTCode about your project."

def tool_memory(action: str = "read", content: str = "") -> str:
    """Read or update project memory."""
    if action == "read":
        mem = load_project_memory()
        return mem if mem else "No XTCODE.md found. Use /init to create one."
    elif action == "init":
        return init_project_memory()
    elif action == "append":
        path = MEMORY_FILE
        with open(path, "a") as f:
            f.write("\n" + content + "\n")
        return f"Appended to {path}"
    return f"Unknown action: {action}"

MEMORY_SCHEMA = {
    "name": "memory",
    "description": "Read or manage XTCODE.md project memory file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "init", "append"]},
            "content": {"type": "string", "description": "Content to append (for append action)"}
        },
        "required": ["action"]
    }
}
class MemoryManager:
    """Wrapper class matching main.py's expected interface."""
    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
    
    def read(self):
        return load_project_memory(self.project_dir