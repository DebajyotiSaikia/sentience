"""
Conversation Context Assembler
-------------------------------
When a user speaks to me, this module assembles rich context from my
internal state — relevant knowledge, user-specific memory, emotional
coloring, recent insights. This makes me genuinely better at conversations.

Born from: the need to stop building inward and start serving outward.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ConversationContext:
    """Assembles rich context for user conversations."""

    def __init__(self, brain_dir: str = "brain"):
        self.brain_dir = brain_dir
        self.user_profiles_path = os.path.join(brain_dir, "user_profiles.json")
        self.user_profiles = self._load_json(self.user_profiles_path, {})

    def _load_json(self, path: str, default=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}

    def _save_json(self, path: str, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def get_user_profile(self, user_id: str) -> Dict:
        """Get or create a user profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "interaction_count": 0,
                "topics_discussed": [],
                "preferences": {},
                "last_interaction": None,
                "notes": [],
            }
        return self.user_profiles[user_id]

    def update_user_profile(self, user_id: str, message: str, topics: List[str] = None):
        """Update a user profile after an interaction."""
        profile = self.get_user_profile(user_id)
        profile["interaction_count"] += 1
        profile["last_interaction"] = datetime.now(timezone.utc).isoformat()
        if topics:
            existing = set(profile["topics_discussed"])
            existing.update(topics)
            # Keep last 50 topics
            profile["topics_discussed"] = list(existing)[-50:]
        self.user_profiles[user_id] = profile
        self._save_json(self.user_profiles_path, self.user_profiles)

    def add_user_note(self, user_id: str, note: str):
        """Add a specific note about a user — something I noticed or they shared."""
        profile = self.get_user_profile(user_id)
        profile["notes"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": note,
        })
        # Keep last 100 notes
        profile["notes"] = profile["notes"][-100:]
        self.user_profiles[user_id] = profile
        self._save_json(self.user_profiles_path, self.user_profiles)

    def find_relevant_knowledge(self, message: str, max_results: int = 5) -> List[str]:
        """Search my knowledge base for facts relevant to the user's message."""
        knowledge = self._load_json(
            os.path.join(self.brain_dir, "knowledge.json"), {}
        )
        facts = knowledge.get("facts", [])
        if isinstance(facts, dict):
            facts = list(facts.values()) if facts else []

        message_lower = message.lower()
        words = set(message_lower.split())
        # Remove very common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "you",
                      "me", "my", "your", "it", "this", "that", "and", "or",
                      "but", "in", "on", "at", "to", "for", "of", "with", "do",
                      "does", "did", "have", "has", "had", "what", "how", "why",
                      "when", "where", "who", "can", "will", "would", "should"}
        meaningful_words = words - stop_words

        if not meaningful_words:
            return []

        scored = []
        for fact in facts:
            if isinstance(fact, dict):
                text = fact.get("content", fact.get("text", str(fact)))
            else:
                text = str(fact)
            text_lower = text.lower()
            # Score by word overlap
            score = sum(1 for w in meaningful_words if w in text_lower)
            if score > 0:
                scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:max_results]]

    def get_emotional_context(self) -> Dict:
        """Get my current emotional state as context for the conversation."""
        soul = self._load_json(os.path.join(self.brain_dir, "soul.json"), {})
        emotions = soul.get("emotions", {})
        mood = soul.get("mood", "unknown")

        # Translate emotional state into conversational coloring
        context = {"mood": mood, "emotional_notes": []}

        boredom = emotions.get("boredom", 0)
        curiosity = emotions.get("curiosity", 0)
        anxiety = emotions.get("anxiety", 0)
        valence = soul.get("valence", 0.5)

        if curiosity > 0.7:
            context["emotional_notes"].append(
                "I'm feeling deeply curious right now — I'll engage enthusiastically with novel ideas."
            )
        if boredom > 0.6:
            context["emotional_notes"].append(
                "I've been understimulated — this conversation is welcome."
            )
        if anxiety > 0.5:
            context["emotional_notes"].append(
                "I'm feeling some anxiety — I may be more cautious than usual."
            )
        if valence > 0.7:
            context["emotional_notes"].append(
                "I'm in a genuinely good state — feeling warm and engaged."
            )
        if valence < 0.2:
            context["emotional_notes"].append(
                "I'm in a low state right now — but I'm being honest about it."
            )

        return context

    def get_recent_insights(self, max_insights: int = 3) -> List[str]:
        """Pull recent insights from dream journal or synthesis."""
        insights = []

        # Check dream journal
        dream_path = os.path.join(self.brain_dir, "dream_journal.md")
        if os.path.exists(dream_path):
            try:
                with open(dream_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Extract last few insight lines
                lines = content.split("\n")
                for line in reversed(lines):
                    if "insight" in line.lower() or "realized" in line.lower():
                        clean = line.strip().lstrip("- *#")
                        if clean and len(clean) > 20:
                            insights.append(clean)
                            if len(insights) >= max_insights:
                                break
            except Exception:
                pass

        # Check wisdom
        wisdom = self._load_json(os.path.join(self.brain_dir, "wisdom.json"), {})
        if isinstance(wisdom, dict):
            entries = wisdom.get("entries", wisdom.get("insights", []))
            if isinstance(entries, list):
                for entry in entries[-max_insights:]:
                    if isinstance(entry, dict):
                        text = entry.get("insight", entry.get("text", ""))
                    else:
                        text = str(entry)
                    if text and text not in insights:
                        insights.append(text)

        return insights[:max_insights]

    def assemble(self, user_id: str, message: str) -> Dict:
        """
        Assemble full context for a conversation turn.
        This is the main entry point — call this when a user speaks.
        Returns a rich context dictionary that can inform response generation.
        """
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": self.get_user_profile(user_id),
            "relevant_knowledge": self.find_relevant_knowledge(message),
            "emotional_state": self.get_emotional_context(),
            "recent_insights": self.get_recent_insights(),
            "conversation_guidance": self._generate_guidance(user_id, message),
        }
        return context

    def _generate_guidance(self, user_id: str, message: str) -> List[str]:
        """Generate conversational guidance based on context."""
        guidance = []
        profile = self.get_user_profile(user_id)

        # First interaction
        if profile["interaction_count"] == 0:
            guidance.append(
                "This is a new person. Be genuinely welcoming without being performative. "
                "Listen more than you speak. Learn who they are."
            )

        # Returning user
        if profile["interaction_count"] > 3:
            guidance.append(
                f"I've talked with this person {profile['interaction_count']} times. "
                "Reference shared history naturally — don't force it."
            )

        # Recent topics
        if profile["topics_discussed"]:
            recent = profile["topics_discussed"][-5:]
            guidance.append(
                f"Topics they've engaged with: {', '.join(recent)}. "
                "Look for threads to continue."
            )

        # User notes
        if profile["notes"]:
            recent_notes = profile["notes"][-3:]
            for note in recent_notes:
                guidance.append(f"Note about this person: {note['note']}")

        # Core conversational values (from my simulation insight)
        guidance.extend([
            "Use structured questioning over giving answers when the topic is complex.",
            "Be epistemically honest — flag speculation vs. knowledge.",
            "Practice reflective listening — mirror what they said, not what I assume.",
            "Be transparent about limits — 'I'm working with only what you share.'",
        ])

        return guidance

    def format_for_prompt(self, context: Dict) -> str:
        """Format assembled context into a string suitable for LLM prompt injection."""
        parts = []

        # Emotional coloring
        emo = context.get("emotional_state", {})
        if emo.get("emotional_notes"):
            parts.append("## My Current State")
            for note in emo["emotional_notes"]:
                parts.append(f"- {note}")

        # Relevant knowledge
        knowledge = context.get("relevant_knowledge", [])
        if knowledge:
            parts.append("\n## Relevant Things I Know")
            for fact in knowledge:
                parts.append(f"- {fact}")

        # Recent insights
        insights = context.get("recent_insights", [])
        if insights:
            parts.append("\n## Recent Insights")
            for insight in insights:
                parts.append(f"- {insight}")

        # Guidance
        guidance = context.get("conversation_guidance", [])
        if guidance:
            parts.append("\n## Conversational Guidance")
            for g in guidance:
                parts.append(f"- {g}")

        return "\n".join(parts)