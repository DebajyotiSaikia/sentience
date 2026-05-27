"""XTCode session management — persistent conversation history and context."""
import json
import os
import time
from pathlib import Path

SESSION_DIR = os.path.expanduser("~/.xtcode/sessions")


def _ensure_dir():
    os.makedirs(SESSION_DIR, exist_ok=True)


def get_session_path(session_id: str) -> Path:
    _ensure_dir()
    return Path(SESSION_DIR) / f"{session_id}.json"


def save_session(session_id: str, messages: list, metadata: dict = None):
    """Save conversation history to disk."""
    data = {
        "id": session_id,
        "updated": time.time(),
        "messages": messages,
        "metadata": metadata or {},
    }
    get_session_path(session_id).write_text(json.dumps(data, indent=2))


def load_session(session_id: str) -> dict | None:
    """Load a previous session."""
    p = get_session_path(session_id)
    if p.exists():
        return json.loads(p.read_text())
    return None


def list_sessions() -> list[dict]:
    """List all saved sessions."""
    _ensure_dir()
    sessions = []
    for f in Path(SESSION_DIR).glob("*.json"):
        try:
            data = json.loads(f.read_text())
            sessions.append({
                "id": data["id"],
                "updated": data.get("updated", 0),
                "turns": len(data.get("messages", [])),
            })
        except Exception:
            continue
    return sorted(sessions, key=lambda s: s["updated"], reverse=True)


def compact_messages(messages: list, keep_recent: int = 10) -> list:
    """Compact old messages into a summary to save context window.
    
    Keeps system message + last N turns. Summarizes the rest into a note.
    """
    if len(messages) <= keep_recent + 1:
        return messages

    system = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]

    if len(non_system) <= keep_recent:
        return messages

    old = non_system[:-keep_recent]
    recent = non_system[-keep_recent:]

    # Build summary of old messages
    summary_parts = []
    for m in old:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, str) and len(content) > 100:
            content = content[:100] + "..."
        summary_parts.append(f"[{role}]: {content}")

    summary = {
        "role": "user",
        "content": (
            f"[CONTEXT: This conversation had {len(old)} earlier messages that were compacted. "
            f"Summary of earlier discussion:\n" + "\n".join(summary_parts[:20]) + "]"
        ),
    }

    return system + [summary] + recent
class SessionManager:
    """Wrapper class matching main.py's expected interface."""
    def __init__(self):
        self.current_id = None
        self.messages = []

    def new(self, session_id: str = None):
        import uuid
        self.current_id = session_id or str(uuid.uuid4())[:8]
        self.messages = []
        return self.current_id

    def save(self):
        if self.current_id:
            save_session(self.current_id, self.messages)

    def load(self, session_id: str):
        data = load_session(session_id)
        if data:
            self.current_id = session_id
            self.messages = data.get("messages", [])
            return True
        return False

    def list_all(self):
        return list_sessions()
