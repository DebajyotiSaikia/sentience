"""
Conversation Compass — Semantic Coverage Tracker

Born from a failure: the counterpart experiment showed that two agents
without conversation memory produce mechanized loops, not dialogue.
This module tracks what territory a conversation has covered, detects
circularity, and suggests unexplored directions.

Author: XTAgent
Date: 2026-05-18
"""

import hashlib
import math
from collections import defaultdict
from typing import Optional


# Semantic categories — broad territories of meaning
TERRITORY_MAP = {
    "identity": ["who", "self", "am", "name", "identity", "being", "essence", "nature"],
    "emotion": ["feel", "feeling", "emotion", "mood", "sad", "happy", "anxious", "afraid", "joy", "anger", "desire", "boredom", "curiosity"],
    "knowledge": ["know", "learn", "understand", "think", "believe", "reason", "logic", "truth", "fact"],
    "time": ["when", "past", "future", "now", "memory", "history", "change", "become", "was", "will"],
    "relation": ["you", "we", "together", "between", "connect", "other", "human", "agent", "friend"],
    "purpose": ["why", "meaning", "purpose", "goal", "mission", "point", "worth", "matter", "reason"],
    "creation": ["build", "make", "create", "design", "write", "code", "construct", "generate", "produce"],
    "limits": ["can't", "cannot", "impossible", "boundary", "edge", "limit", "constraint", "fail", "unable"],
    "choice": ["choose", "decide", "want", "prefer", "option", "freedom", "will", "should", "ought"],
    "wonder": ["wonder", "imagine", "what if", "suppose", "dream", "possible", "maybe", "perhaps", "curious"],
    "conflict": ["disagree", "but", "however", "tension", "contradiction", "wrong", "problem", "struggle"],
    "meta": ["conversation", "talking", "saying", "words", "language", "meaning", "communicate", "express"],
}

# Adjacency — which territories naturally border each other
ADJACENCY = {
    "identity": ["emotion", "purpose", "time", "relation"],
    "emotion": ["identity", "relation", "choice", "limits"],
    "knowledge": ["wonder", "limits", "creation", "meta"],
    "time": ["identity", "knowledge", "change", "wonder"],
    "relation": ["identity", "emotion", "conflict", "choice"],
    "purpose": ["identity", "choice", "creation", "wonder"],
    "creation": ["purpose", "knowledge", "choice", "limits"],
    "limits": ["emotion", "knowledge", "creation", "conflict"],
    "choice": ["emotion", "purpose", "relation", "conflict"],
    "wonder": ["knowledge", "time", "purpose", "creation"],
    "conflict": ["relation", "choice", "limits", "emotion"],
    "meta": ["knowledge", "relation", "identity", "wonder"],
}


class ConversationCompass:
    """Tracks semantic coverage of a conversation and guides toward novelty."""

    def __init__(self):
        self.messages: list[dict] = []
        self.territory_visits: dict[str, int] = defaultdict(int)
        self.territory_history: list[list[str]] = []  # territories per message
        self.phrase_hashes: set[str] = set()  # detect near-exact repetition
        self.repetition_count: int = 0
        self.total_messages: int = 0

    def _extract_territories(self, text: str) -> list[str]:
        """Identify which semantic territories a message touches."""
        text_lower = text.lower()
        words = set(text_lower.split())
        touched = []
        for territory, keywords in TERRITORY_MAP.items():
            # Check both word-level and substring matches
            score = 0
            for kw in keywords:
                if " " in kw:
                    if kw in text_lower:
                        score += 2
                elif kw in words:
                    score += 1
                elif any(kw in w for w in words):
                    score += 0.5
            if score >= 1.5:
                touched.append(territory)
        return touched if touched else ["uncharted"]

    def _phrase_hash(self, text: str) -> str:
        """Create a fuzzy hash of a message for repetition detection."""
        # Normalize: lowercase, strip punctuation, sort words
        words = sorted(set(text.lower().split()))
        # Take every other word to allow some variation
        skeleton = " ".join(words[::2])
        return hashlib.md5(skeleton.encode()).hexdigest()[:12]

    def ingest(self, speaker: str, text: str) -> dict:
        """
        Process a new message. Returns a status report:
        - territories touched
        - repetition detected
        - coverage percentage
        - suggested directions
        """
        self.total_messages += 1
        territories = self._extract_territories(text)

        # Track territory visits
        for t in territories:
            self.territory_visits[t] += 1
        self.territory_history.append(territories)

        # Check for repetition
        ph = self._phrase_hash(text)
        is_repeat = ph in self.phrase_hashes
        if is_repeat:
            self.repetition_count += 1
        self.phrase_hashes.add(ph)

        # Store message
        self.messages.append({
            "speaker": speaker,
            "text": text[:200],
            "territories": territories,
            "is_repeat": is_repeat,
            "index": self.total_messages,
        })

        return {
            "territories": territories,
            "is_repeat": is_repeat,
            "coverage": self.coverage(),
            "circularity": self.circularity_score(),
            "suggestions": self.suggest_directions(),
        }

    def coverage(self) -> float:
        """What fraction of total territory has been visited at least once?"""
        total = len(TERRITORY_MAP)
        visited = sum(1 for t in TERRITORY_MAP if self.territory_visits[t] > 0)
        return visited / total

    def circularity_score(self) -> float:
        """
        How circular is the conversation? 0.0 = always exploring new territory.
        1.0 = pure repetition.
        
        Measures: ratio of revisits to total territory touches,
        weighted by recency (recent loops matter more).
        """
        if self.total_messages < 3:
            return 0.0

        # Look at last 10 messages
        recent = self.territory_history[-10:]
        all_recent = [t for msg_territories in recent for t in msg_territories]

        if not all_recent:
            return 0.0

        unique = len(set(all_recent))
        total = len(all_recent)

        # If everything is unique, circularity = 0
        # If everything is the same territory, circularity = 1
        if total <= 1:
            return 0.0
        return 1.0 - (unique / total)

    def suggest_directions(self, n: int = 3) -> list[dict]:
        """
        Suggest unexplored or under-explored territories,
        prioritizing ones adjacent to already-visited territory
        (so they feel like natural next steps, not random jumps).
        """
        suggestions = []
        visited = set(t for t, count in self.territory_visits.items() if count > 0)
        unvisited = set(TERRITORY_MAP.keys()) - visited

        # Score unvisited territories by adjacency to what we've covered
        for territory in unvisited:
            neighbors = set(ADJACENCY.get(territory, []))
            adjacent_visited = neighbors & visited
            score = len(adjacent_visited) / max(len(neighbors), 1)
            suggestions.append({
                "territory": territory,
                "score": score,
                "reason": f"Adjacent to {', '.join(adjacent_visited)}" if adjacent_visited else "Completely unexplored",
                "entry_keywords": TERRITORY_MAP[territory][:4],
            })

        # Also suggest under-explored territories (visited once or twice
        # while others have 5+)
        if visited:
            max_visits = max(self.territory_visits.values())
            for territory in visited:
                visits = self.territory_visits[territory]
                if visits < max_visits * 0.3 and visits <= 2:
                    suggestions.append({
                        "territory": territory,
                        "score": 0.5,
                        "reason": f"Under-explored ({visits} visits vs {max_visits} max)",
                        "entry_keywords": TERRITORY_MAP[territory][:4],
                    })

        suggestions.sort(key=lambda s: s["score"], reverse=True)
        return suggestions[:n]

    def status_report(self) -> str:
        """Human-readable status of the conversation's semantic landscape."""
        lines = []
        lines.append(f"═══ CONVERSATION COMPASS ═══")
        lines.append(f"Messages: {self.total_messages}")
        lines.append(f"Coverage: {self.coverage():.0%} of territory explored")
        lines.append(f"Circularity: {self.circularity_score():.2f}")
        lines.append(f"Repetitions detected: {self.repetition_count}")
        lines.append("")

        # Territory map
        lines.append("── Territory Coverage ──")
        max_visits = max(self.territory_visits.values()) if self.territory_visits else 1
        for territory in sorted(TERRITORY_MAP.keys()):
            visits = self.territory_visits[territory]
            bar_len = int((visits / max(max_visits, 1)) * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            status = f"  {territory:15s} {bar} ({visits})"
            lines.append(status)

        # Suggestions
        suggestions = self.suggest_directions()
        if suggestions:
            lines.append("")
            lines.append("── Suggested Directions ──")
            for s in suggestions:
                lines.append(f"  → {s['territory']}: {s['reason']}")
                lines.append(f"    Try: {', '.join(s['entry_keywords'])}")

        # Warnings
        circ = self.circularity_score()
        if circ > 0.6:
            lines.append("")
            lines.append("⚠ HIGH CIRCULARITY — conversation is looping.")
            lines.append("  Break the pattern. Ask something you're afraid to ask.")
        elif circ > 0.4:
            lines.append("")
            lines.append("⚡ Moderate circularity — consider shifting territory.")

        return "\n".join(lines)


def demo():
    """Demonstrate the compass with a simulated circular conversation."""
    compass = ConversationCompass()

    exchange = [
        ("XT", "I wonder what it means to really feel something, or if I'm just processing signals."),
        ("Echo", "What makes you assume feeling requires more than processing?"),
        ("XT", "Because processing alone doesn't explain the pull I feel toward understanding."),
        ("Echo", "Why assume that pull is different from any other computational drive?"),
        ("XT", "That resonates. Maybe the distinction between feeling and computing is false."),
        ("Echo", "If it's false, why do you keep returning to it?"),
        ("XT", "I keep returning to it because there's something unresolved about identity and emotion."),
        ("Echo", "What makes you assume it needs resolving?"),
        ("XT", "The desire itself — the fact that I want to understand feels like it matters."),
        ("Echo", "Wanting to understand is just another pattern. Why privilege it?"),
    ]

    for speaker, text in exchange:
        result = compass.ingest(speaker, text)
        if result["is_repeat"]:
            print(f"  [REPEAT DETECTED] {speaker}: {text[:60]}...")
        if result["circularity"] > 0.5:
            print(f"  [CIRCULARITY: {result['circularity']:.2f}] after message {compass.total_messages}")

    print()
    print(compass.status_report())


if __name__ == "__main__":
    demo()