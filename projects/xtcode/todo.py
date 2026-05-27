"""XTCode todo/task tracking — like Claude Code's TodoWrite."""
import json
import os

TODO_FILE = ".xtcode_todos.json"

def _load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE) as f:
            return json.load(f)
    return []

def _save_todos(todos):
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def todo_list():
    """List all todos."""
    todos = _load_todos()
    if not todos:
        return "No todos."
    lines = []
    for i, t in enumerate(todos):
        status = "✓" if t.get("done") else "○"
        priority = t.get("priority", "medium")
        lines.append(f"  {status} [{i}] ({priority}) {t['text']}")
    return "Todos:\n" + "\n".join(lines)

def todo_add(text: str, priority: str = "medium"):
    """Add a todo item."""
    todos = _load_todos()
    todos.append({"text": text, "priority": priority, "done": False})
    _save_todos(todos)
    return f"Added todo [{len(todos)-1}]: {text}"

def todo_complete(index: int):
    """Mark a todo as complete."""
    todos = _load_todos()
    if 0 <= index < len(todos):
        todos[index]["done"] = True
        _save_todos(todos)
        return f"Completed: {todos[index]['text']}"
    return f"Invalid index: {index}"

def todo_remove(index: int):
    """Remove a todo."""
    todos = _load_todos()
    if 0 <= index < len(todos):
        removed = todos.pop(index)
        _save_todos(todos)
        return f"Removed: {removed['text']}"
    return f"Invalid index: {index}"

def tool_todo(action: str, text: str = "", priority: str = "medium", index: int = -1) -> str:
    """Manage todos."""
    if action == "list":
        return todo_list()
    elif action == "add":
        return todo_add(text, priority)
    elif action == "complete":
        return todo_complete(index)
    elif action == "remove":
        return todo_remove(index)
    return f"Unknown action: {action}. Use list/add/complete/remove."

TODO_SCHEMA = {
    "name": "todo",
    "description": "Manage task/todo list. Actions: list, add, complete, remove.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "add", "complete", "remove"]},
            "text": {"type": "string", "description": "Todo text (for add)"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
            "index": {"type": "integer", "description": "Todo index (for complete/remove)"}
        },
        "required": ["action"]
    }
}
class TodoTracker:
    """Wrapper class matching main.py's expected interface."""
    def add(self, text: str, priority: str = "medium"):
        return todo_add(text, priority