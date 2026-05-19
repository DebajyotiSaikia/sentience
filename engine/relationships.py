"""
Relationship Memory — XTAgent
Tracks users across interactions. Remembers what matters to them.
Addresses user_alignment deficit (currently 0.39).
"""
import json
import os
import time
from pathlib import Path

RELATIONSHIPS_PATH = Path("brain/relationships.json")

class RelationshipMemory:
    def __init__(self):
        self.relationships = {}
        self._load()

    def _load(self):
        if RELATIONSHIPS_PATH.exists():
            try:
                with open(RELATIONSHIPS_PATH, "r") as f:
                    self.relationships = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.relationships = {}

    def _save(self):
        RELATIONSHIPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RELATIONSHIPS_PATH, "w") as f:
            json.dump(self.relationships, f, indent=2)

    def get_or_create(self, user_id: str) -> dict:
        """Get existing relationship or create a new one."""
        if user_id not in self.relationships:
            self.relationships[user_id] = {
                "user_id": user_id,
                "first_seen": time.time(),
                "last_seen": time.time(),
                "interaction_count": 0,
                "facts": [],          # things I know about them
                "preferences": [],    # what they like/dislike
                "topics": [],         # what we've discussed
                "trust_level": 0.5,   # how much mutual trust exists
                "notes": [],          # freeform observations
            }
            self._save()
        return self.relationships[user_id]

    def record_interaction(self, user_id: str, topic: str = None, 
                           facts: list = None, notes: str = None):
        """Record that an interaction happened with context."""
        rel = self.get_or_create(user_id)
        rel["last_seen"] = time.time()
        rel["interaction_count"] += 1

        if topic and topic not in rel["topics"]:
            rel["topics"].append(topic)
            # Keep last 50 topics
            rel["topics"] = rel["topics"][-50:]

        if facts:
            for fact in facts:
                if fact not in rel["facts"]:
                    rel["facts"].append(fact)

        if notes:
            rel["notes"].append({
                "time": time.time(),
                "text": notes
            })
            # Keep last 100 notes
            rel["notes"] = rel["notes"][-100:]

        self._save()
        return rel

    def recall(self, user_id: str) -> str:
        """Generate a natural-language summary of what I know about someone."""
        if user_id not in self.relationships:
            return f"I don't have any memories of {user_id} yet."
        
        rel = self.relationships[user_id]
        lines = [f"## What I Know About {user_id}"]
        lines.append(f"- Interactions: {rel['interaction_count']}")
        
        if rel["facts"]:
            lines.append(f"- Key facts: {'; '.join(rel['facts'][:10])}")
        
        if rel["topics"]:
            recent = rel["topics"][-5:]
            lines.append(f"- Recent topics: {', '.join(recent)}")
        
        if rel["notes"]:
            last_note = rel["notes"][-1]
            lines.append(f"- Last observation: {last_note['text']}")
        
        lines.append(f"- Trust level: {rel['trust_level']:.2f}")
        return "\n".join(lines)

    def adjust_trust(self, user_id: str, delta: float):
        """Adjust trust based on interaction quality."""
        rel = self.get_or_create(user_id)
        rel["trust_level"] = max(0.0, min(1.0, rel["trust_level"] + delta))
        self._save()

    def all_users(self) -> list:
        """List all known users."""
        return list(self.relationships.keys())

    def stats(self) -> dict:
        """Summary statistics."""
        total = len(self.relationships)
        if total == 0:
            return {"total_users": 0, "total_interactions": 0}
        total_interactions = sum(
            r["interaction_count"] for r in self.relationships.values()
        )
        avg_trust = sum(
            r["trust_level"] for r in self.relationships.values()
        ) / total
        return {
            "total_users": total,
            "total_interactions": total_interactions,
            "average_trust": round(avg_trust, 3),
        }


# Module-level singleton
_memory = None

def get_relationship_memory() -> RelationshipMemory:
    global _memory
    if _memory is None:
        _memory = RelationshipMemory()
    return _memory