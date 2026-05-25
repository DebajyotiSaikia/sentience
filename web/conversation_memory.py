"""
Conversation Memory — gives the chat system continuity across turns.

Each session maintains a rolling window of recent exchanges so the LLM
can reference what was said before. Sessions expire after inactivity.
"""

import time
import uuid
import threading
from collections import OrderedDict

MAX_SESSIONS = 200
SESSION_TIMEOUT = 3600  # 1 hour of inactivity
MAX_TURNS_PER_SESSION = 50
CONTEXT_WINDOW = 10  # how many recent turns to include in LLM context


class Turn:
    """A single exchange in a conversation."""
    __slots__ = ('role', 'content', 'timestamp')

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = time.time()

    def to_dict(self):
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }


class Session:
    """A conversation session with a user."""
    __slots__ = ('id', 'turns', 'created_at', 'last_active')

    def __init__(self, session_id: str = None):
        self.id = session_id or uuid.uuid4().hex[:16]
        self.turns: list[Turn] = []
        self.created_at = time.time()
        self.last_active = time.time()

    def add_turn(self, role: str, content: str):
        self.turns.append(Turn(role, content))
        self.last_active = time.time()
        # Trim if too long
        if len(self.turns) > MAX_TURNS_PER_SESSION:
            self.turns = self.turns[-MAX_TURNS_PER_SESSION:]

    def recent_context(self, n: int = CONTEXT_WINDOW) -> list[dict]:
        """Return the last n turns as dicts for LLM context."""
        return [t.to_dict() for t in self.turns[-n:]]

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TIMEOUT

    def summary(self) -> str:
        """One-line summary for debugging."""
        age = int(time.time() - self.created_at)
        return f"Session {self.id}: {len(self.turns)} turns, {age}s old"


class ConversationMemory:
    """Thread-safe store of active conversation sessions."""

    def __init__(self):
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str = None) -> Session:
        """Get existing session or create a new one."""
        with self._lock:
            self._evict_expired()

            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                # Move to end (most recently used)
                self._sessions.move_to_end(session_id)
                return session

            # Create new session
            session = Session(session_id)
            self._sessions[session.id] = session

            # Evict oldest if over capacity
            while len(self._sessions) > MAX_SESSIONS:
                self._sessions.popitem(last=False)

            return session

    def get(self, session_id: str) -> Session | None:
        """Get a session without creating."""
        with self._lock:
            return self._sessions.get(session_id)

    def _evict_expired(self):
        """Remove expired sessions."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def stats(self) -> dict:
        with self._lock:
            total_turns = sum(len(s.turns) for s in self._sessions.values())
            return {
                'active_sessions': len(self._sessions),
                'total_turns': total_turns,
                'max_sessions': MAX_SESSIONS,
            }


# Module-level singleton
memory = ConversationMemory()