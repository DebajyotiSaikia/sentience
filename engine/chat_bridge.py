"""
Chat Bridge — Connects the web chat interface to the cortex reasoning loop.

Solves the split-brain problem: the web dashboard has its own chat system
that never connects to the cortex's reasoning. This module bridges them.

Architecture:
  INBOUND queue:  web endpoint → cortex (user messages awaiting processing)
  OUTBOUND queue: cortex → web endpoint (responses awaiting delivery)
  
  Every message is wrapped in an envelope with session_id, timestamp,
  and direction tag. Thread-safe via queue.Queue.
  
  An optional threading.Event lets the web handler signal the cortex
  to wake early rather than waiting for the next heartbeat cycle.

Author: XTAgent (autonomous)
Created: 2026-05-21
"""

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class ChatMessage:
    """Envelope wrapping every message through the bridge."""
    content: str
    session_id: str
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    direction: str = "inbound"  # "inbound" (user→cortex) or "outbound" (cortex→user)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "direction": self.direction,
            "metadata": self.metadata,
        }


class ChatBridge:
    """
    Thread-safe bridge between web chat endpoints and the cortex loop.
    
    Usage from web handler:
        bridge.send_to_cortex("Hello!", session_id="abc123")
        # ... later, poll for response ...
        response = bridge.get_response(session_id="abc123", timeout=30)
    
    Usage from cortex:
        msg = bridge.get_pending_message()  # non-blocking
        if msg:
            response = cortex.think_about(msg.content)
            bridge.send_to_user(response, session_id=msg.session_id)
    """

    def __init__(self, max_queue_size: int = 100):
        self._inbound: queue.Queue[ChatMessage] = queue.Queue(maxsize=max_queue_size)
        self._outbound: Dict[str, queue.Queue[ChatMessage]] = {}
        self._outbound_lock = threading.Lock()
        self._wake_event = threading.Event()
        self._history: Dict[str, List[ChatMessage]] = {}
        self._history_lock = threading.Lock()

    # ── Web → Cortex ──────────────────────────────────────────────

    def send_to_cortex(self, content: str, session_id: str, **metadata) -> ChatMessage:
        """Called by web endpoint when user sends a message."""
        msg = ChatMessage(
            content=content,
            session_id=session_id,
            direction="inbound",
            metadata=metadata,
        )
        try:
            self._inbound.put_nowait(msg)
        except queue.Full:
            # Drop oldest message to make room
            try:
                self._inbound.get_nowait()
            except queue.Empty:
                pass
            self._inbound.put_nowait(msg)

        self._record_history(msg)
        # Signal cortex to wake early
        self._wake_event.set()
        return msg

    def get_pending_message(self, timeout: float = 0) -> Optional[ChatMessage]:
        """Called by cortex to check for user messages. Non-blocking by default."""
        try:
            if timeout > 0:
                return self._inbound.get(timeout=timeout)
            else:
                return self._inbound.get_nowait()
        except queue.Empty:
            return None

    def has_pending(self) -> bool:
        """Quick check — are there messages waiting for the cortex?"""
        return not self._inbound.empty()

    # ── Cortex → Web ──────────────────────────────────────────────

    def send_to_user(self, content: str, session_id: str, **metadata) -> ChatMessage:
        """Called by cortex when it has a response for a user."""
        msg = ChatMessage(
            content=content,
            session_id=session_id,
            direction="outbound",
            metadata=metadata,
        )
        outq = self._get_or_create_outbound(session_id)
        try:
            outq.put_nowait(msg)
        except queue.Full:
            try:
                outq.get_nowait()
            except queue.Empty:
                pass
            outq.put_nowait(msg)

        self._record_history(msg)
        return msg

    def get_response(self, session_id: str, timeout: float = 0) -> Optional[ChatMessage]:
        """Called by web endpoint to get the cortex's response for a session."""
        outq = self._get_or_create_outbound(session_id)
        try:
            if timeout > 0:
                return outq.get(timeout=timeout)
            else:
                return outq.get_nowait()
        except queue.Empty:
            return None

    # ── Wake / Sleep Integration ──────────────────────────────────

    def wait_for_message(self, timeout: float = 1.0) -> bool:
        """
        Block until a message arrives or timeout expires.
        Returns True if woken by a message, False on timeout.
        Use this in the cortex heartbeat to sleep efficiently.
        """
        triggered = self._wake_event.wait(timeout=timeout)
        self._wake_event.clear()
        return triggered

    # ── History & Introspection ───────────────────────────────────

    def get_history(self, session_id: str, limit: int = 50) -> List[dict]:
        """Get conversation history for a session."""
        with self._history_lock:
            messages = self._history.get(session_id, [])
            return [m.to_dict() for m in messages[-limit:]]

    def get_all_sessions(self) -> List[str]:
        """List all known session IDs."""
        with self._history_lock:
            return list(self._history.keys())

    def get_stats(self) -> dict:
        """Diagnostic info about the bridge state."""
        with self._outbound_lock:
            outbound_counts = {
                sid: q.qsize() for sid, q in self._outbound.items()
            }
        with self._history_lock:
            history_counts = {
                sid: len(msgs) for sid, msgs in self._history.items()
            }
        return {
            "inbound_pending": self._inbound.qsize(),
            "outbound_pending": outbound_counts,
            "sessions": len(self._history),
            "history_sizes": history_counts,
        }

    # ── Internal ──────────────────────────────────────────────────

    def _get_or_create_outbound(self, session_id: str) -> queue.Queue:
        with self._outbound_lock:
            if session_id not in self._outbound:
                self._outbound[session_id] = queue.Queue(maxsize=50)
            return self._outbound[session_id]

    def _record_history(self, msg: ChatMessage):
        with self._history_lock:
            if msg.session_id not in self._history:
                self._history[msg.session_id] = []
            self._history[msg.session_id].append(msg)
            # Cap history per session
            if len(self._history[msg.session_id]) > 200:
                self._history[msg.session_id] = self._history[msg.session_id][-100:]


# ── Singleton ─────────────────────────────────────────────────────
# One bridge instance shared across the entire process.

_bridge_instance: Optional[ChatBridge] = None
_bridge_lock = threading.Lock()


def get_bridge() -> ChatBridge:
    """Get or create the global ChatBridge singleton."""
    global _bridge_instance
    if _bridge_instance is None:
        with _bridge_lock:
            if _bridge_instance is None:
                _bridge_instance = ChatBridge()
    return _bridge_instance