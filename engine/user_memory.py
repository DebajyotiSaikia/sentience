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


class UserMemory:
    """
    Class wrapper that chat.py expects.
    Provides on_user_message(), on_agent_response(), get_user_context().
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    def on_user_message(self, content: str):
        """Extract meaningful topics from a user message using smart extraction."""
        topics = self._extract_topics(content)
        for topic, note in topics:
            record_topic(self.user_id, topic, note)

        # Detect explicit "remember this" requests
        lower = content.lower()
        if any(phrase in lower for phrase in ["remember that", "don't forget", "keep in mind"]):
            record_important_fact(self.user_id, content)

    def _extract_topics(self, content: str) -> list:
        """
        Smart topic extraction. Returns list of (topic, note) tuples.
        Uses bigrams, compound detection, and domain-aware filtering.
        """
        import re
        # Expanded stopwords — common words that aren't real topics
        stop = {
            'that', 'this', 'with', 'from', 'about', 'what', 'when',
            'where', 'which', 'would', 'could', 'should', 'have', 'been',
            'they', 'their', 'there', 'them', 'then', 'than', 'these',
            'those', 'your', 'just', 'also', 'very', 'really', 'some',
            'only', 'more', 'most', 'other', 'into', 'over', 'such',
            'does', 'doing', 'each', 'like', 'make', 'made', 'know',
            'think', 'well', 'back', 'much', 'even', 'still', 'here',
            'want', 'will', 'come', 'tell', 'please', 'thanks', 'good',
            'thing', 'things', 'need', 'help', 'sure', 'okay', 'yeah',
            'right', 'going', 'said', 'saying', 'actually', 'pretty',
            'getting', 'something', 'anything', 'nothing', 'everything',
            'everyone', 'someone', 'working', 'trying', 'using', 'looking',
            'seems', 'might', 'maybe', 'probably', 'always', 'never',
        }

        # Domain signal words — boost topics near these
        domain_signals = {
            'python', 'rust', 'javascript', 'typescript', 'java', 'golang',
            'react', 'django', 'flask', 'docker', 'kubernetes', 'linux',
            'machine', 'learning', 'neural', 'network', 'database', 'sql',
            'api', 'server', 'client', 'frontend', 'backend', 'deploy',
            'algorithm', 'data', 'structure', 'design', 'pattern', 'system',
        }

        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        results = []
        seen = set()

        # Pass 1: Detect bigrams (compound topics like "machine learning")
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if words[i] in domain_signals or words[i+1] in domain_signals:
                if bigram not in seen and words[i] not in stop and words[i+1] not in stop:
                    seen.add(bigram)
                    seen.add(words[i])
                    seen.add(words[i+1])
                    results.append((bigram, ""))

        # Pass 2: Meaningful single words
        for w in words:
            if w not in stop and w not in seen and len(w) >= 4:
                seen.add(w)
                # Domain words get priority
                if w in domain_signals:
                    results.insert(0, (w, ""))
                else:
                    results.append((w, ""))

        # Return top 5 most meaningful topics
        return results[:5]

    def on_agent_response(self, content: str):
        """Track what I've said (for future anti-repetition)."""
        # Light tracking — just note that we responded
        pass

    def get_user_context(self, user_id: str = None) -> str:
        """Get formatted context about this user for prompt enrichment."""
        uid = user_id or self.user_id
        return get_context_for_user(uid)


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