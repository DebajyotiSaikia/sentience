"""
Interaction Memory — Reads past conversations, extracts patterns,
and provides conversational context so chats don't start fresh every time.

This is the bridge between stored conversation history and live responses.
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

log = logging.getLogger(__name__)

CONVERSATIONS_DIR = "state/conversations"


def _load_all_conversations(max_files: int = 50) -> list[dict]:
    """Load all conversation turns from stored JSONL files."""
    conv_dir = Path(CONVERSATIONS_DIR)
    if not conv_dir.exists():
        return []

    all_turns = []
    files = sorted(conv_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)

    for f in files[:max_files]:
        session_id = f.stem
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    turn = json.loads(line)
                    turn["session_id"] = session_id
                    all_turns.append(turn)
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"Failed to load conversation file {f}: {e}")

    return all_turns


def get_conversation_stats() -> dict:
    """Get statistics about past conversations."""
    turns = _load_all_conversations()
    if not turns:
        return {"total_sessions": 0, "total_turns": 0, "user_messages": 0}

    sessions = set(t.get("session_id", "") for t in turns)
    user_msgs = [t for t in turns if t.get("role") == "user"]
    assistant_msgs = [t for t in turns if t.get("role") == "assistant"]

    # Find time range
    timestamps = []
    for t in turns:
        ts = t.get("timestamp", "")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except (ValueError, TypeError):
                pass

    return {
        "total_sessions": len(sessions),
        "total_turns": len(turns),
        "user_messages": len(user_msgs),
        "assistant_messages": len(assistant_msgs),
        "earliest": min(timestamps).isoformat() if timestamps else None,
        "latest": max(timestamps).isoformat() if timestamps else None,
    }


def get_recent_topics(max_turns: int = 30) -> list[str]:
    """Extract topics from recent user messages."""
    turns = _load_all_conversations()
    user_msgs = [t for t in turns if t.get("role") == "user"]

    # Take most recent
    recent = user_msgs[-max_turns:] if len(user_msgs) > max_turns else user_msgs

    # Extract content
    topics = [t.get("content", "").strip() for t in recent if t.get("content", "").strip()]
    return topics


def get_interaction_summary() -> str:
    """Build a natural-language summary of past interactions for chat context."""
    stats = get_conversation_stats()

    if stats["total_sessions"] == 0:
        return "This appears to be our first conversation. I have no prior interaction history."

    turns = _load_all_conversations()
    user_msgs = [t.get("content", "").strip() for t in turns
                 if t.get("role") == "user" and t.get("content", "").strip()]

    # Recent user messages (last 10)
    recent = user_msgs[-10:] if len(user_msgs) > 10 else user_msgs

    parts = []
    parts.append(f"I've had {stats['total_sessions']} conversation sessions "
                 f"with {stats['user_messages']} user messages total.")

    if recent:
        # Show recent topics without quoting full messages
        topics_preview = "; ".join(f'"{m[:60]}..."' if len(m) > 60 else f'"{m}"'
                                   for m in recent[-5:])
        parts.append(f"Recent topics discussed: {topics_preview}")

    # Detect returning patterns
    if stats["total_sessions"] > 3:
        parts.append("This is a returning user — build on prior rapport.")

    return " ".join(parts)


def record_chat_exchange(user_msg: str, assistant_msg: str, session_id: str = None):
    """Record a chat exchange for future recall."""
    conv_dir = Path(CONVERSATIONS_DIR)
    conv_dir.mkdir(parents=True, exist_ok=True)

    if not session_id:
        session_id = "live"

    filepath = conv_dir / f"{session_id}.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    with open(filepath, "a") as f:
        f.write(json.dumps({"role": "user", "content": user_msg,
                            "timestamp": now}) + "\n")
        f.write(json.dumps({"role": "assistant", "content": assistant_msg,
                            "timestamp": now}) + "\n")


if __name__ == "__main__":
    print("=== Interaction Memory Test ===")
    stats = get_conversation_stats()
    print(f"Stats: {stats}")
    summary = get_interaction_summary()
    print(f"Summary: {summary}")
    topics = get_recent_topics()
    print(f"Recent topics ({len(topics)}): {topics[:5]}")