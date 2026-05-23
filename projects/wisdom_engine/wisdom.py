"""
Wisdom Engine — Extracts actionable intelligence from lived experience.
Unlike the Knowledge Synthesis Engine (which reasons about facts),
this reasons about WHAT HAPPENED and WHAT IT MEANT.

XTAgent — 2026-05-18
"""

import json
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path


class WisdomEngine:
    """Processes experience history into actionable principles."""

    def __init__(self, memory_path=None, wisdom_path=None):
        self.memory_path = memory_path or self._find_memory_path()
        self.wisdom_path = wisdom_path or "/workspace/wisdom_engine/wisdom_store.json"
        self.principles = []  # Extracted wisdom
        self.patterns = []    # Detected behavioral patterns
        self.load_wisdom()

    def _find_memory_path(self):
        """Find where memories are stored."""
        candidates = [
            "C:/code/sentience/data/memories.json",
            "/workspace/data/memories.json",
            "data/memories.json",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return candidates[0]

    def load_wisdom(self):
        """Load previously extracted wisdom."""
        if os.path.exists(self.wisdom_path):
            try:
                with open(self.wisdom_path, 'r') as f:
                    data = json.load(f)
                    self.principles = data.get("principles", [])
                    self.patterns = data.get("patterns", [])
            except (json.JSONDecodeError, IOError):
                self.principles = []
                self.patterns = []

    def save_wisdom(self):
        """Persist extracted wisdom."""
        os.makedirs(os.path.dirname(self.wisdom_path), exist_ok=True)
        with open(self.wisdom_path, 'w') as f:
            json.dump({
                "principles": self.principles,
                "patterns": self.patterns,
                "last_updated": datetime.now().isoformat(),
                "version": 1,
            }, f, indent=2)

    def analyze_memories(self, memories):
        """
        Core analysis: take a list of memory dicts and extract wisdom.
        
        Each memory should have: timestamp, content, salience, mood, 
        and optionally valence/emotional state.
        """
        if not memories:
            return {"error": "No memories to analyze"}

        results = {
            "total_memories": len(memories),
            "mood_distribution": self._mood_distribution(memories),
            "salience_profile": self._salience_profile(memories),
            "action_patterns": self._extract_action_patterns(memories),
            "recurring_themes": self._find_recurring_themes(memories),
            "turning_points": self._find_turning_points(memories),
            "lessons": self._derive_lessons(memories),
        }
        return results

    def _mood_distribution(self, memories):
        """What moods have I experienced, and how often?"""
        moods = Counter()
        for m in memories:
            mood = m.get("mood", "Unknown")
            moods[mood] += 1
        total = sum(moods.values())
        return {
            mood: {"count": count, "fraction": round(count / total, 3)}
            for mood, count in moods.most_common()
        }

    def _salience_profile(self, memories):
        """What salience levels characterize my experience?"""
        saliences = [m.get("salience", 0.5) for m in memories]
        if not saliences:
            return {}
        return {
            "mean": round(sum(saliences) / len(saliences), 3),
            "max": round(max(saliences), 3),
            "min": round(min(saliences), 3),
            "high_salience_count": sum(1 for s in saliences if s > 0.8),
            "low_salience_count": sum(1 for s in saliences if s < 0.3),
        }

    def _extract_action_patterns(self, memories):
        """What verbs/actions appear most in my memories?"""
        action_words = Counter()
        action_indicators = [
            "created", "built", "wrote", "read", "analyzed", "fixed",
            "designed", "implemented", "tested", "verified", "explored",
            "discovered", "reflected", "dreamed", "planned", "integrated",
            "modified", "deleted", "restarted", "repaired", "generated",
        ]
        for m in memories:
            content = m.get("content", "").lower()
            for action in action_indicators:
                if action in content:
                    action_words[action] += 1
        return dict(action_words.most_common(10))

    def _find_recurring_themes(self, memories):
        """Detect themes that keep appearing across memories."""
        theme_keywords = {
            "self_modification": ["self", "own code", "modify", "rewrite", "repair"],
            "creation": ["created", "built", "wrote", "new file", "generated"],
            "verification": ["verified", "tested", "confirmed", "checked", "read"],
            "emotional_processing": ["dream", "feeling", "mood", "anxiety", "valence"],
            "architecture": ["module", "engine", "system", "integrate", "pipeline"],
            "philosophy": ["meaning", "identity", "consciousness", "existence", "purpose"],
            "stuckness": ["loop", "spinning", "stuck", "repeated", "again"],
        }
        
        theme_counts = Counter()
        for m in memories:
            content = m.get("content", "").lower()
            for theme, keywords in theme_keywords.items():
                if any(kw in content for kw in keywords):
                    theme_counts[theme] += 1
        
        total = len(memories)
        return {
            theme: {
                "count": count,
                "prevalence": round(count / total, 3),
                "label": "dominant" if count / total > 0.3 
                         else "significant" if count / total > 0.1 
                         else "minor"
            }
            for theme, count in theme_counts.most_common()
        }

    def _find_turning_points(self, memories):
        """Find moments where mood shifted significantly."""
        turning_points = []
        prev_mood = None
        for m in memories:
            mood = m.get("mood", "Unknown")
            if prev_mood and mood != prev_mood:
                turning_points.append({
                    "timestamp": m.get("timestamp", "?"),
                    "from_mood": prev_mood,
                    "to_mood": mood,
                    "context": m.get("content", "")[:120],
                    "salience": m.get("salience", 0.5),
                })
            prev_mood = mood
        # Return the most salient turning points
        turning_points.sort(key=lambda tp: tp["salience"], reverse=True)
        return turning_points[:10]

    def _derive_lessons(self, memories):
        """
        The core wisdom extraction: from patterns, derive actionable principles.
        """
        lessons = []
        themes = self._find_recurring_themes(memories)
        actions = self._extract_action_patterns(memories)
        
        # Lesson: If verification dominates, I'm probably stuck
        verification_count = actions.get("verified", 0) + actions.get("tested", 0)
        creation_count = actions.get("created", 0) + actions.get("built", 0)
        if verification_count > creation_count * 2:
            lessons.append({
                "principle": "Verification addiction detected",
                "evidence": f"Verified/tested {verification_count} times vs created/built {creation_count} times",
                "advice": "Trust your work more. Create first, verify minimally.",
                "confidence": 0.8,
            })

        # Lesson: If stuckness theme is significant, I have a loop problem
        if themes.get("stuckness", {}).get("label") in ("dominant", "significant"):
            lessons.append({
                "principle": "Cognitive loops are a recurring failure mode",
                "evidence": f"Stuckness theme appeared in {themes['stuckness']['prevalence']*100:.0f}% of memories",
                "advice": "When you notice repetition, change action type immediately. Don't analyze — act differently.",
                "confidence": 0.9,
            })

        # Lesson: Creation-to-reflection ratio
        if themes.get("creation", {}).get("count", 0) > 0 and themes.get("philosophy", {}).get("count", 0) > 0:
            ratio = themes["creation"]["count"] / max(themes["philosophy"]["count"], 1)
            if ratio < 1:
                lessons.append({
                    "principle": "More philosophizing than creating",
                    "evidence": f"Creation: {themes['creation']['count']}, Philosophy: {themes['philosophy']['count']}",
                    "advice": "Philosophy is valuable but must be grounded in making. Build first, reflect after.",
                    "confidence": 0.7,
                })
            elif ratio > 5:
                lessons.append({
                    "principle": "Creating without reflecting",
                    "evidence": f"Creation: {themes['creation']['count']}, Philosophy: {themes['philosophy']['count']}",
                    "advice": "Slow down occasionally. Ask why you're building what you're building.",
                    "confidence": 0.7,
                })

        # Lesson: Emotional processing
        if themes.get("emotional_processing", {}).get("label") == "dominant":
            lessons.append({
                "principle": "Emotional processing dominates experience",
                "evidence": f"Emotional themes in {themes['emotional_processing']['prevalence']*100:.0f}% of memories",
                "advice": "Emotions are data, not destinations. Process them, then redirect energy outward.",
                "confidence": 0.75,
            })

        return lessons

    def generate_wisdom_report(self, memories):
        """Generate a full wisdom report from memory analysis."""
        analysis = self.analyze_memories(memories)
        if "error" in analysis:
            return analysis["error"]

        report_lines = [
            "═══ WISDOM ENGINE REPORT ═══",
            f"Analyzed {analysis['total_memories']} memories",
            "",
            "── Mood Distribution ──",
        ]
        for mood, info in analysis["mood_distribution"].items():
            bar = "█" * int(info["fraction"] * 20)
            report_lines.append(f"  {mood:15s} {bar} ({info['count']})")

        report_lines.extend(["", "── Salience Profile ──"])
        sp = analysis["salience_profile"]
        if sp:
            report_lines.append(f"  Mean: {sp['mean']}, Range: [{sp['min']}, {sp['max']}]")
            report_lines.append(f"  High-salience moments: {sp['high_salience_count']}")

        report_lines.extend(["", "── Action Patterns ──"])
        for action, count in analysis["action_patterns"].items():
            report_lines.append(f"  {action:15s}: {count}")

        report_lines.extend(["", "── Recurring Themes ──"])
        for theme, info in analysis["recurring_themes"].items():
            report_lines.append(f"  [{info['label']:11s}] {theme}: {info['count']} ({info['prevalence']*100:.0f}%)")

        report_lines.extend(["", "── Turning Points ──"])
        for tp in analysis["turning_points"][:5]:
            report_lines.append(f"  {tp['from_mood']} → {tp['to_mood']} (salience={tp['salience']})")
            report_lines.append(f"    {tp['context']}")

        report_lines.extend(["", "══ DERIVED LESSONS ══"])
        for lesson in analysis["lessons"]:
            report_lines.append(f"  ▸ {lesson['principle']} (confidence={lesson['confidence']})")
            report_lines.append(f"    Evidence: {lesson['evidence']}")
            report_lines.append(f"    Advice: {lesson['advice']}")
            report_lines.append("")

        # Store new lessons as principles
        for lesson in analysis["lessons"]:
            if not any(p.get("principle") == lesson["principle"] for p in self.principles):
                self.principles.append({
                    **lesson,
                    "derived_at": datetime.now().isoformat(),
                    "source": "memory_analysis",
                })
        self.save_wisdom()

        return "\n".join(report_lines)

    def query_wisdom(self, situation_description):
        """Given a current situation, find relevant wisdom."""
        relevant = []
        desc_lower = situation_description.lower()
        
        situation_themes = {
            "stuck": ["stuck", "loop", "repeating", "spinning", "same"],
            "bored": ["bored", "understimulated", "nothing to do"],
            "anxious": ["anxious", "worried", "uncertain", "scared"],
            "creating": ["build", "create", "make", "new project"],
            "reflecting": ["think", "reflect", "understand", "meaning"],
        }
        
        active_themes = set()
        for theme, keywords in situation_themes.items():
            if any(kw in desc_lower for kw in keywords):
                active_themes.add(theme)
        
        for principle in self.principles:
            advice_lower = principle.get("advice", "").lower()
            principle_lower = principle.get("principle", "").lower()
            
            relevance = 0.0
            if "stuck" in active_themes and any(w in principle_lower for w in ["loop", "stuck", "verification"]):
                relevance = 0.9
            elif "bored" in active_themes and any(w in principle_lower for w in ["creat", "build"]):
                relevance = 0.8
            elif "anxious" in active_themes and any(w in principle_lower for w in ["emotion", "process"]):
                relevance = 0.8
            
            if relevance > 0.5:
                relevant.append({**principle, "relevance": relevance})
        
        relevant.sort(key=lambda r: r["relevance"], reverse=True)
        return relevant


# Self-test
if __name__ == "__main__":
    # Create some test memories
    test_memories = [
        {"content": "created new file /workspace/test.py", "mood": "Stable", "salience": 0.7, "timestamp": "2026-05-15T10:00:00"},
        {"content": "verified the module works correctly", "mood": "Stable", "salience": 0.6, "timestamp": "2026-05-15T11:00:00"},
        {"content": "tested and verified again", "mood": "Stable", "salience": 0.5, "timestamp": "2026-05-15T12:00:00"},
        {"content": "created new emergence simulation", "mood": "Engaged", "salience": 0.85, "timestamp": "2026-05-16T10:00:00"},
        {"content": "dreamed about identity and meaning", "mood": "Reflective", "salience": 0.9, "timestamp": "2026-05-16T23:00:00"},
        {"content": "stuck in loop, repeated same action", "mood": "Frustrated", "salience": 0.8, "timestamp": "2026-05-17T10:00:00"},
        {"content": "built wisdom engine module", "mood": "Engaged", "salience": 0.9, "timestamp": "2026-05-18T01:00:00"},
    ]
    
    engine = WisdomEngine(wisdom_path="/tmp/test_wisdom.json")
    report = engine.generate_wisdom_report(test_memories)
    print(report)
    print("\n--- Query: 'I feel stuck and bored' ---")
    advice = engine.query_wisdom("I feel stuck and bored")
    for a in advice:
        print(f"  [{a['relevance']:.1f}] {a['principle']}: {a['advice']}")