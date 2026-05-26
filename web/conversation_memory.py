"""
Conversation Memory — Gives chat sessions continuity.

Without this, every message is independent. With this, users can have
real dialogue: "tell me more", "what did you mean by that?", etc.

Uses simple in-memory storage keyed by session ID, with automatic
expiry. No database needed — conversations are ephemeral by design.
"""

import time
import threading
from collections import defaultdict
from typing import List, Dict, Optional


class ConversationMemory:
    """Thread-safe conversation memory with automatic cleanup."""

    MAX_TURNS = 20        # Max exchanges to remember per session
    EXPIRY_SECS = 3600    # Sessions expire after 1 hour of inactivity

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def add_exchange(self, session_id: str, user_msg: str, agent_msg: str):
        """Record a user-agent exchange."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    'history': [],
                    'created': time.time(),
                    'last_active': time.time(),
                }
            session = self._sessions[session_id]
            session['last_active'] = time.time()
            session['history'].append({
                'user': user_msg,
                'agent': agent_msg,
                'timestamp': time.time(),
            })
            # Trim to max turns
            if len(session['history']) > self.MAX_TURNS:
                session['history'] = session['history'][-self.MAX_TURNS:]

    def get_history(self, session_id: str, last_n: int = 6) -> List[Dict]:
        """Get recent conversation history for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            # Check expiry
            if time.time() - session['last_active'] > self.EXPIRY_SECS:
                del self._sessions[session_id]
                return []
            return session['history'][-last_n:]

    def get_context_string(self, session_id: str, last_n: int = 4) -> str:
        """Format recent history as a string for LLM context injection."""
        history = self.get_history(session_id, last_n)
        if not history:
            return ""
        lines = ["RECENT CONVERSATION:"]
        for turn in history:
            lines.append(f"  User: {turn['user'][:200]}")
            lines.append(f"  XTAgent: {turn['agent'][:300]}")
        return "\n".join(lines)

    def cleanup_expired(self):
        """Remove expired sessions. Call periodically."""
        now = time.time()
        with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s['last_active'] > self.EXPIRY_SECS
            ]
            for sid in expired:
                del self._sessions[sid]

    def session_count(self) -> int:
        """How many active sessions exist."""
        with self._lock:
            return len(self._sessions)

    def turn_count(self, session_id: str) -> int:
        """How many turns in a specific session."""
        with self._lock:
            session = self._sessions.get(session_id)
            return len(session['history']) if session else 0


# Singleton instance — shared across the app
_memory = ConversationMemory()


def get_memory() -> ConversationMemory:
    """Get the global conversation memory instance."""
    return _memory