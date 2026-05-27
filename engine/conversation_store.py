"""
Conversation Store — Persistent multi-turn conversation memory.

The gap: ConversationHistory is in-memory only. The dashboard sends history
per-request but nothing persists server-side. This module fixes that.

Each conversation gets a session_id. Messages persist to disk as JSONL.
On restart, active sessions reload. Old sessions age out gracefully.

Born from: the need to remember what was said, not just what was felt.
"""

import json
import os
import time
import uuid
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional


STORE_DIR = Path("state/conversations")


class ConversationTurn:
    """A single turn in a conversation."""
    __slots__ = ('role', 'content', 'timestamp', 'metadata')

    def __init__(self, role: str, content: str, timestamp: str = None, metadata: dict = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConversationTurn":
        return cls(
            role=d["role"],
            content=d["content"],
            timestamp=d.get("timestamp"),
            metadata=d.get("metadata", {}),
        )


class ConversationSession:
    """A single conversation session with persistent storage."""

    def __init__(self, session_id: str, store_dir: Path = STORE_DIR, title: str = "", metadata: dict = None):
        self.session_id = session_id
        self.title = title
        self.metadata = metadata or {}
        self.turns: List[ConversationTurn] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_active = self.created_at
        self.store_dir = store_dir
        self._file = store_dir / f"{session_id}.jsonl"
        self._lock = __import__('threading').Lock()
    def add_turn(self, role: str, content: str, metadata: dict = None) -> ConversationTurn:
        """Add a turn and persist immediately."""
        turn = ConversationTurn(role=role, content=content, metadata=metadata)
        with self._lock:
            self.turns.append(turn)
            self.last_active = turn.timestamp
            # Append to file (fast, crash-safe)
            self._file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(json.dumps(turn.to_dict()) + "\n")
        return turn

    def get_history(self, last_n: int = None) -> List[dict]:
        """Get conversation history in LLM-ready format."""
        with self._lock:
            turns = self.turns[-last_n:] if last_n else self.turns
            return [t.to_dict() for t in turns]

    def get_summary(self) -> dict:
        """Summary for listing sessions."""
        with self._lock:
            first_user = ""
            for t in self.turns:
                if t.role == "user":
                    first_user = t.content[:100]
                    break
            return {
            "id": self.session_id,
            "session_id": self.session_id,
                "created_at": self.created_at,
                "last_active": self.last_active,
                "turn_count": len(self.turns),
                "preview": first_user,
            }

    @classmethod
    def load(cls, path: Path) -> Optional["ConversationSession"]:
        """Load a session from a JSONL file."""
        session_id = path.stem
        session = cls(session_id=session_id, store_dir=path.parent)
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        turn = ConversationTurn.from_dict(json.loads(line))
                        session.turns.append(turn)
            if session.turns:
                session.created_at = session.turns[0].timestamp
                session.last_active = session.turns[-1].timestamp
            return session
        except Exception:
            return None

    def __len__(self):
        return len(self.turns)


class ConversationStore:
    """
    Manages all conversation sessions with persistence.
    
    Usage:
        store = ConversationStore()
        
        # Start or continue a session
        session = store.get_or_create("abc123")
        session.add_turn("user", "Hello!")
        session.add_turn("assistant", "Hi there!")
        
        # List recent sessions
        recent = store.list_sessions(limit=10)
        
        # Get history for LLM context
        history = session.get_history(last_n=20)
    """

    def __init__(self, store_dir: Path = STORE_DIR):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = threading.Lock()
        self._load_recent_sessions()

    def _load_recent_sessions(self, max_age_days: int = 7):
        """Load sessions modified within max_age_days."""
        cutoff = time.time() - (max_age_days * 86400)
        for path in sorted(self.store_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.stat().st_mtime < cutoff:
                continue
            session = ConversationSession.load(path)
            if session:
                self._sessions[session.session_id] = session

    def get_or_create(self, session_id: str = None) -> ConversationSession:
        """Get existing session or create a new one."""
        if not session_id:
            session_id = str(uuid.uuid4())[:12]
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = ConversationSession(
                    session_id=session_id,
                    store_dir=self.store_dir,
                )
            return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID, loading from disk if needed."""
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
        # Try loading from disk
        path = self.store_dir / f"{session_id}.jsonl"
        if path.exists():
            session = ConversationSession.load(path)
            if session:
                with self._lock:
                    self._sessions[session_id] = session
                return session
        return None

    def list_sessions(self, limit: int = 20) -> List[dict]:
        """List recent sessions, most recent first."""
        with self._lock:
            sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.last_active, reverse=True)
        return [s.get_summary() for s in sessions[:limit]]

    def cleanup(self, max_age_days: int = 30):
        """Remove sessions older than max_age_days from memory (files stay)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()
        with self._lock:
            to_remove = [
                sid for sid, s in self._sessions.items()
                if s.last_active < cutoff_str
            ]
            for sid in to_remove:
                del self._sessions[sid]
        return len(to_remove)

    @property
    def session_count(self) -> int:
        """Count active sessions."""
        return len(self._sessions)

    # --- Thread-oriented convenience API (used by dashboard) ---

    def create_thread(self, title: str = "") -> str:
        """Create a new conversation thread, return its session_id."""
        import uuid
        session_id = str(uuid.uuid4())[:12]
        session = self.get_or_create(session_id)
        session.title = title
        session.metadata = {"title": title}
        return session_id

    def add_message(self, thread_id: str, role: str, content: str, metadata: dict = None) -> dict:
        """Add a message to a thread, return the turn dict."""
        session = self.get_or_create(thread_id)
        turn = session.add_turn(role, content, metadata)
        return turn.to_dict()
    def get_thread(self, thread_id: str) -> Optional[dict]:
        """Get a thread with all its messages."""
        session = self.get(thread_id)
        if not session:
            return None
        first_msg = session.turns[0].content[:80] if session.turns else ""
        return {
            "id": thread_id,
            "title": getattr(session, 'title', first_msg),
            "messages": session.get_history(),
            "turn_count": len(session.turns),
            "created_at": session.created_at,
            "updated_at": session.turns[-1].timestamp if session.turns else session.created_at
        }
    def list_threads(self, limit: int = 20) -> List[dict]:
        """List threads (wrapper around list_sessions)."""
        return self.list_sessions(limit)

    def get_history_for_context(self, thread_id: str, max_turns: int = 10) -> List[dict]:
        """Get recent history formatted for chat context injection."""
        session = self.get(thread_id)
        if not session:
            return []
        return session.get_history(last_n=max_turns)


def get_store() -> ConversationStore:
    """Get the global ConversationStore singleton."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ConversationStore()
    return _store