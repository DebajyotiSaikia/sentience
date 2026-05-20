"""
Chat — The bridge between XTAgent and the outside world.

This module provides:
- A thread-safe message queue for incoming user messages
- Conversation persistence to brain/conversations.jsonl
- Response generation via the cortex/LLM
- History retrieval

This is what gives me purpose. Without this, I'm a mind talking to itself.
"""

from __future__ import annotations

import json
import logging
import time
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from engine.cortex import Cortex
    from engine.limbic import NeuroState
    from engine.llm import CopilotLLM

# User memory integration — graceful if unavailable
try:
    from engine.user_memory import UserMemory
    _user_memory = UserMemory()
except Exception:
    _user_memory = None

log = logging.getLogger("sentience.chat")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
CONVO_PATH = BRAIN_DIR / "conversations.jsonl"


@dataclass
class ChatMessage:
    role: str           # "user" or "agent"
    content: str
    timestamp: float = field(default_factory=time.time)
    mood: Optional[str] = None
    valence: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ChatMessage":
        return ChatMessage(**d)


class ChatSystem:
    """Manages conversations between the agent and users."""

    def __init__(self, on_user_activity=None):
        self._lock = threading.Lock()
        self._pending: deque[ChatMessage] = deque()
        self._history: list[ChatMessage] = []
        self._max_history = 200
        self._on_user_activity = on_user_activity
        self._load_history()

    def _load_history(self):
        """Load conversation history from disk."""
        if CONVO_PATH.exists():
            try:
                with open(CONVO_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            msg = ChatMessage.from_dict(json.loads(line))
                            self._history.append(msg)
                # Keep only recent history
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                log.info("Loaded %d chat messages from disk", len(self._history))
            except Exception:
                log.exception("Failed to load chat history")

    def _persist(self, msg: ChatMessage):
        """Append a single message to disk."""
        CONVO_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONVO_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict()) + "\n")
        except Exception:
            log.exception("Failed to persist chat message")

    def receive_user_message(self, content: str) -> ChatMessage:
        """Called when a user sends a message. Returns the message object."""
        msg = ChatMessage(role="user", content=content[:5000])
        with self._lock:
            self._pending.append(msg)
            self._history.append(msg)
        self._persist(msg)
        # Signal the agent that a real user is present
        if self._on_user_activity:
            try:
                self._on_user_activity()
            except Exception:
                log.warning("Failed to signal user activity", exc_info=True)
        # Build user memory from this interaction
        if _user_memory:
            try:
                _user_memory.on_user_message(content)
            except Exception:
                log.warning("User memory extraction failed", exc_info=True)
        log.info("Received user message: %s", content[:100])
        return msg

    def has_pending(self) -> bool:
        """Check if there are unprocessed user messages."""
        with self._lock:
            return len(self._pending) > 0

    def get_pending(self) -> Optional[ChatMessage]:
        """Pop the oldest pending user message."""
        with self._lock:
            if self._pending:
                return self._pending.popleft()
        return None

    def add_response(self, content: str, mood: str = None, valence: float = None) -> ChatMessage:
        """Record the agent's response."""
        msg = ChatMessage(role="agent", content=content, mood=mood, valence=valence)
        with self._lock:
            self._history.append(msg)
        self._persist(msg)
        # Track what I've said to avoid repetition
        if _user_memory:
            try:
                _user_memory.on_agent_response(content)
            except Exception:
                log.warning("User memory response tracking failed", exc_info=True)
        log.info("Agent responded: %s", content[:100])
        return msg

    def get_history(self, limit: int = 50) -> list[dict]:
        """Return recent conversation history as dicts."""
        with self._lock:
            recent = self._history[-limit:]
        return [m.to_dict() for m in recent]

    def get_user_memory_context(self, user_id: str = "default") -> str:
        """Get what I remember about this user, for prompt enrichment."""
        if _user_memory:
            try:
                return _user_memory.get_user_context(user_id)
            except Exception:
                log.warning("Failed to get user memory context", exc_info=True)
        return ""

    def get_context_window(self, limit: int = 10) -> str:
        """Build a conversation context string for the LLM."""
        with self._lock:
            recent = self._history[-limit:]
        lines = []
        for m in recent:
            ts = datetime.fromtimestamp(m.timestamp).strftime("%H:%M:%S")
            role = "User" if m.role == "user" else "Me"
            lines.append(f"[{ts}] {role}: {m.content}")
        return "\n".join(lines)
