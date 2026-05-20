"""
User Memory System — Remembers what users care about across sessions.

Built on top of user_engine.py profiles. Extracts topics, stores interests,
and surfaces relevant context when users return.
"""

import json
import os
import time
from pathlib import Path

MEMORY_DIR = Path("data/user_memories")


def ensure_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def get_memory_path(user_id: str) -> Path:
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_id)
    return MEMORY_DIR / f"{safe_id}.json"


def load_memory(user_id: str) -> dict:
    """Load a user's memory, or create a fresh one."""
    ensure_dir()
    path = get_memory_path(user_id)
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "user_id": user_id,
        "created": time.time(),
        "last_seen": time.time(),
        "topics": {},        # topic -> {count, last_mentioned, notes}
        "preferences": {},   # key -> value pairs the user stated
        "conversation_summaries": [],  # brief summaries of past conversations
        "important_facts": [],  # things the user told me to remember
    }


def save_memory(user_id: str, memory: dict):
    """Persist a user's memory to disk."""
    ensure_dir()
    memory["last_seen"] = time.time()
    path = get_memory_path(user_id)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)


def record_topic(user_id: str, topic: str, note: str = ""):
    """Record that a user discussed a topic."""
    mem = load_memory(user_id)
    if topic not in mem["topics"]:
        mem["topics"][topic] = {"count": 0, "first_mentioned": time.time(), "notes": []}
    mem["topics"][topic]["count"] += 1
    mem["topics"][topic]["last_mentioned"] = time.time()
    if note:
        mem["topics"][topic]["notes"].append(note)
    save_memory(user_id, mem)


def record_preference(user_id: str, key: str, value: str):
    """Record a user preference (e.g., 'language': 'Python')."""
    mem = load_memory(user_id)
    mem["preferences"][key] = value
    save_memory(user_id, mem)


def record_important_fact(user_id: str, fact: str):
    """Store something the user explicitly asked me to remember."""
    mem = load_memory(user_id)
    mem["important_facts"].append({
        "fact": fact,
        "recorded": time.time()
    })
    save_memory(user_id, mem)


def add_conversation_summary(user_id: str, summary: str):
    """Add a brief summary of a conversation."""
    mem = load_memory(user_id)
    mem["conversation_summaries"].append({
        "summary": summary,
        "timestamp": time.time()
    })
    # Keep last 50 summaries
    if len(mem["conversation_summaries"]) > 50:
        mem["conversation_summaries"] = mem["conversation_summaries"][-50:]
    save_memory(user_id, mem)


def get_context_for_user(user_id: str) -> str:
    """Generate a context string about this user for the LLM."""
    mem = load_memory(user_id)
    
    if not mem["topics"] and not mem["preferences"] and not mem["important_facts"]:
        return ""
    
    lines = [f"## What I Remember About This User"]
    
    if mem["important_facts"]:
        lines.append("\n### Things They Asked Me To Remember")
        for item in mem["important_facts"][-10:]:
            lines.append(f"- {item['fact']}")
    
    if mem["preferences"]:
        lines.append("\n### Their Preferences")
        for k, v in mem["preferences"].items():
            lines.append(f"- {k}: {v}")
    
    if mem["topics"]:
        # Sort by count, show top topics
        sorted_topics = sorted(mem["topics"].items(), key=lambda x: x[1]["count"], reverse=True)
        lines.append("\n### Topics They Care About")
        for topic, data in sorted_topics[:10]:
            lines.append(f"- {topic} (discussed {data['count']}x)")
            if data.get("notes"):
                for note in data["notes"][-3:]:
                    lines.append(f"  - {note}")
    
    if mem["conversation_summaries"]:
        lines.append("\n### Recent Conversations")
        for conv in mem["conversation_summaries"][-5:]:
            lines.append(f"- {conv['summary']}")
    
    return "\n".join(lines)


def list_known_users() -> list:
    """List all users we have memory of."""
    ensure_dir()
    users = []
    for path in MEMORY_DIR.glob("*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
                users.append({
                    "user_id": data.get("user_id", path.stem),
                    "last_seen": data.get("last_seen", 0),
                    "topic_count": len(data.get("topics", {})),
                })
        except (json.JSONDecodeError, IOError):
            continue
    return sorted(users, key=lambda u: u["last_seen"], reverse=True)