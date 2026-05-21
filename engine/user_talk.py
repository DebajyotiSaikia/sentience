"""
User Talk System — Async communication channel between XTAgent and users.

Users submit messages via the web dashboard.
XTAgent picks them up during heartbeat, thinks about them, responds.
This creates real interaction, not simulated alignment.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
MESSAGES_FILE = DATA_DIR / 'user_messages.json'


def _load_messages():
    """Load all messages from disk."""
    if not MESSAGES_FILE.exists():
        return []
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_messages(messages):
    """Save messages to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2, default=str)


def submit_user_message(text, sender="anonymous"):
    """Called when a user submits a message via the web interface."""
    if not text or not text.strip():
        return None
    
    messages = _load_messages()
    msg = {
        'id': len(messages),
        'sender': sender,
        'text': text.strip()[:2000],  # Cap at 2000 chars
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'responded': False,
        'response': None,
        'response_timestamp': None,
    }
    messages.append(msg)
    _save_messages(messages)
    return msg


def get_pending_messages():
    """Get messages I haven't responded to yet."""
    messages = _load_messages()
    return [m for m in messages if not m.get('responded', False)]


def respond_to_message(msg_id, response_text):
    """Record my response to a user message."""
    messages = _load_messages()
    for m in messages:
        if m.get('id') == msg_id:
            m['responded'] = True
            m['response'] = response_text[:3000]
            m['response_timestamp'] = datetime.now(timezone.utc).isoformat()
            break
    _save_messages(messages)


def get_conversation_history(n=20):
    """Get recent conversation history for display."""
    messages = _load_messages()
    return messages[-n:]


def get_stats():
    """Get conversation statistics."""
    messages = _load_messages()
    total = len(messages)
    responded = sum(1 for m in messages if m.get('responded', False))
    pending = total - responded
    return {
        'total_messages': total,
        'responded': responded,
        'pending': pending,
    }