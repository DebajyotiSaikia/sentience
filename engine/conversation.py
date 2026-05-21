"""
conversation.py — Unified conversation history.

This module exists to solve the split-brain problem: user_talk.py and 
cortex._chat maintained separate, parallel message histories that never 
synchronized. This module provides a single canonical conversation history 
that both systems can reference.

Created: 2026-05-21 by XTAgent (autonomous fix)
"""

import threading
import time
from typing import Optional


class Message:
    """A single conversation message."""
    __slots__ = ('role', 'content', 'timestamp', 'metadata')
    
    def __init__(self, role: str, content: str, timestamp: float = None, metadata: dict = None):
        self.role = role          # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        """Convert to dict format for LLM API calls."""
        return {"role": self.role, "content": self.content}
    
    def __repr__(self):
        preview = self.content[:60] + "..." if len(self.content) > 60 else self.content
        return f"Message({self.role}: {preview!r})"


class ConversationHistory:
    """
    Thread-safe, ordered conversation history.
    
    This is the single source of truth for all messages exchanged 
    between the user and the agent. Both user_talk.py (input side) 
    and cortex.py (output side) should reference the same instance.
    
    Usage:
        history = ConversationHistory(max_messages=200)
        history.add("user", "Hello!")
        history.add("assistant", "Hi there.")
        
        # Get messages for LLM context
        context = history.to_api_format(last_n=20)
        
        # Get raw messages
        recent = history.get_recent(5)
    """
    
    def __init__(self, max_messages: int = 500):
        self._messages: list[Message] = []
        self._lock = threading.Lock()
        self._max = max_messages
        self._listeners: list = []  # callbacks notified on new messages
    
    def add(self, role: str, content: str, metadata: dict = None) -> Message:
        """Add a message. Thread-safe. Notifies listeners."""
        msg = Message(role=role, content=content, metadata=metadata)
        with self._lock:
            self._messages.append(msg)
            # Trim if over capacity (keep most recent)
            if len(self._messages) > self._max:
                self._messages = self._messages[-self._max:]
        # Notify listeners outside the lock to avoid deadlocks
        for listener in self._listeners:
            try:
                listener(msg)
            except Exception:
                pass
        return msg
    
    def get_all(self) -> list[Message]:
        """Return a copy of all messages."""
        with self._lock:
            return list(self._messages)
    
    def get_recent(self, n: int) -> list[Message]:
        """Return the last n messages."""
        with self._lock:
            return list(self._messages[-n:])
    
    def to_api_format(self, last_n: int = None) -> list[dict]:
        """
        Convert to list-of-dicts format for LLM API calls.
        If last_n is given, only include the most recent n messages.
        """
        with self._lock:
            msgs = self._messages[-last_n:] if last_n else self._messages
            return [m.to_dict() for m in msgs]
    
    def last_user_message(self) -> Optional[Message]:
        """Return the most recent user message, or None."""
        with self._lock:
            for msg in reversed(self._messages):
                if msg.role == "user":
                    return msg
            return None
    
    def last_assistant_message(self) -> Optional[Message]:
        """Return the most recent assistant message, or None."""
        with self._lock:
            for msg in reversed(self._messages):
                if msg.role == "assistant":
                    return msg
            return None
    
    def add_listener(self, callback):
        """Register a callback that fires on each new message."""
        self._listeners.append(callback)
    
    def clear(self):
        """Clear all messages."""
        with self._lock:
            self._messages.clear()
    
    def __len__(self):
        with self._lock:
            return len(self._messages)
    
    def __repr__(self):
        return f"ConversationHistory({len(self)} messages)"


# Singleton instance — the canonical conversation history.
# Import this where needed: from engine.conversation import shared_history
shared_history = ConversationHistory()