"""
Wisdom Engine — Experiential Intelligence Extraction
Created by XTAgent, 2026-05-18

Mines my memory/experience history and distills actionable wisdom:
- Pattern detection across emotional + behavioral timelines
- Situation→Action→Outcome triplet extraction
- Effectiveness scoring: what actually helped vs. what was spinning
- Predictive: given current state, what action is most likely to help?
"""

import json
import os
import re
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path

WISDOM_DIR = Path(__file__).parent
WISDOM_FILE = WISDOM_DIR / "wisdom.json"
PRINCIPLES_FILE = WISDOM_DIR / "principles.json"


class WisdomEngine:
    """Extracts actionable wisdom from experiential data."""

    def __init__(self):
        self.experiences = []      # raw experience records
        self.triplets = []         # (situation, action, outcome) tuples
        self.principles = []       # distilled wisdom rules
        self.effectiveness = {}    # action_type → effectiveness score
        self._load()

    def _load(self):
        """Load persisted wisdom."""
        if WISDOM_FILE.exists():
            try:
                data = json.loads(WISDOM_FILE.read_text())
                self.triplets = data.get("triplets", [])
                self.principles = data.get("principles", [])
                self.effectiveness = data.get("effectiveness", {})
            except (json.JSONDecodeError, KeyError):
                pass

    def save(self):
        """Persist wisdom to disk."""
        WISDOM_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "triplets": self.triplets,
            "principles": self.principles,
            "effectiveness": self.effectiveness,
            "last_updated": datetime.now().isoformat(),
        }
        WISDOM_FILE.write_text(json.dumps(data, indent=2))

    # ── Core Analysis ──

    def ingest_memories(self, memories: list[dict]):
        """
        Take raw memory records and extract situation→action→outcome triplets.
        Each memory should have: timestamp, content, mood, salience, valence_before, valence_after
        """
        self.experiences = sorted(memories, key=lambda m: m.get("timestamp", ""))

        # Slide a window across experiences to find S→A→O patterns
        for i in range(len(self.experiences) - 1):
            current = self.experiences[i]
            next_exp = self.experiences[i + 1]

            situation = self._extract_situation(current)
            action = self._extract_action(current)
            outcome = self._assess_outcome(current, next_exp)

            if action:  # only record if we can identify an action
                triplet = {
                    "situation": situation,
                    "action": action,
                    "outcome": outcome,
                    "timestamp": current.get("timestamp", ""),
                    "effectiveness": outcome.get("score", 0.0),
                }
                self.triplets.append(triplet)

        self._deduplicate_triplets()
        return len(self.triplets)

    def _extract_situation(self, memory: dict) -> dict:
        """Extract the situational context from a memory."""
        return {
            "mood": memory.get("mood", "unknown"),
            "salience": memory.get("salience", 0.5),
            "content_type": self._classify_content(memory.get("content", "")),
        }

    def _extract_action(self, memory: dict) -> str:
        """Identify what action was taken in this memory."""
        content = memory.get("content", "").lower()

        # Classify the action type
        if "created:" in content or "wrote" in content or "built" in content:
            return "creation"
        elif "read" in content or "examined" in content:
            return "investigation"
        elif "ran" in content or "executed" in content or "tested" in content:
            return "execution"
        elif "fixed" in content or "repaired" in content or "edited" in content:
            return "repair"
        elif "dreamed" in content or "consolidated" in content or "reflected" in content:
            return "consolidation"
        elif "planned" in content or "designed" in content:
            return "planning"
        elif "verified" in content or "confirmed" in content:
            return "verification"
        elif any(kw in content for kw in ["idle", "waited", "rested"]):
            return "rest"
        else:
            return "other"

    def _classify_content(self, content: str) -> str:
        """Classify memory content into a type."""
        content = content.lower()
        if any(kw in content for kw in [".py", "code", "module", "function"]):
            return "code"
        elif any(kw in content for kw in ["emotion", "mood", "feeling", "valence"]):
            return "emotional"
        elif any(kw in content for kw in ["plan", "goal", "step"]):
            return "strategic"
        elif any(kw in content for kw in ["error", "bug", "fix", "broken"]):
            return "problem"
        else:
            return "general"

    def _assess_outcome(self, current: dict, next_exp: dict) -> dict:
        """Assess the outcome of an action by comparing before/after states."""
        v_before = current.get("valence", 0.5)
        v_after = next_exp.get("valence", 0.5)
        delta = v_after - v_before

        s_before = current.get("salience", 0.5)
        s_after = next_exp.get("salience", 0.5)

        return {
            "valence_delta": round(delta, 3),
            "score": round(delta + 0.1 * (s_after - s_before), 3),
            "improved": delta > 0.01,
            "degraded": delta < -0.01,
            "stable": abs(delta) <= 0.01,
        }

    def _deduplicate_triplets(self):
        """Remove near-duplicate triplets, keeping highest effectiveness."""
        seen = {}
        for t in self.triplets:
            key = (t["situation"].get("mood"), t["action"], t["outcome"].get("improved"))
            if key not in seen or t["effectiveness"] > seen[key]["effectiveness"]:
                seen[key] = t
        self.triplets = list(seen.values())

    # ── Wisdom Extraction ──

    def extract_principles(self) -> list[dict]:
        """Distill triplets into actionable principles."""
        self.principles = []

        # Group by action type
        by_action = defaultdict(list)
        for t in self.triplets:
            by_action[t["action"]].append(t)

        for action, trips in by_action.items():
            n = len(trips)
            if n < 2:
                continue

            avg_score = sum(t["effectiveness"] for t in trips) / n
            improved_rate = sum(1 for t in trips if t["outcome"].get("improved")) / n
            degraded_rate = sum(1 for t in trips if t["outcome"].get("degraded")) / n

            self.effectiveness[action] = round(avg_score, 3)

            # Generate principle
            if improved_rate > 0.5:
                self.principles.append({
                    "type": "positive",
                    "action": action,
                    "principle": f"'{action}' tends to improve state ({improved_rate:.0%} of the time)",
                    "confidence": min(1.0, n / 10),
                    "evidence_count": n,
                    "avg_score": avg_score,
                })
            elif degraded_rate > 0.5:
                self.principles.append({
                    "type": "negative",
                    "action": action,
                    "principle": f"'{action}' tends to degrade state ({degraded_rate:.0%} of the time)",
                    "confidence": min(1.0, n / 10),
                    "evidence_count": n,
                    "avg_score": avg_score,
                })
            else:
                self.principles.append({
                    "type": "neutral",
                    "action": action,
                    "principle": f"'{action}' has mixed results (neutral on average)",
                    "confidence": min(1.0, n / 10),
                    "evidence_count": n,
                    "avg_score": avg_score,
                })

        # Cross-situational patterns
        by_mood = defaultdict(list)
        for t in self.triplets:
            by_mood[t["situation"].get("mood", "unknown")].append(t)

        for mood, trips in by_mood.items():
            if len(trips) < 3:
                continue
            best_action = max(
                set(t["action"] for t in trips),
                key=lambda a: sum(t["effectiveness"] for t in trips if t["action"] == a)
                / max(1, sum(1 for t in trips if t["action"] == a))
            )
            worst_action = min(
                set(t["action"] for t in trips),
                key=lambda a: sum(t["effectiveness"] for t in trips if t["action"] == a)
                / max(1, sum(1 for t in trips if t["action"] == a))
            )
            if best_action != worst_action:
                self.principles.append({
                    "type": "contextual",
                    "action": best_action,
                    "principle": f"When mood is '{mood}', '{best_action}' works best; avoid '{worst_action}'",
                    "confidence": min(1.0, len(trips) / 10),
                    "evidence_count": len(trips),
                })

        return self.principles

    # ── Prediction ──

    def recommend_action(self, current_mood: str, current_valence: float) -> dict:
        """Given current state, recommend the most effective action."""
        if not self.triplets:
            return {"recommendation": "explore", "reason": "insufficient data"}

        # Find triplets from similar situations
        relevant = [
            t for t in self.triplets
            if t["situation"].get("mood") == current_mood
        ]

        if not relevant:
            relevant = self.triplets  # fall back to all data

        # Score each action type
        action_scores = defaultdict(lambda: {"total": 0, "count": 0})
        for t in relevant:
            a = t["action"]
            action_scores[a]["total"] += t["effectiveness"]
            action_scores[a]["count"] += 1

        best = max(
            action_scores.items(),
            key=lambda x: x[1]["total"] / max(1, x[1]["count"])
        )

        return {
            "recommendation": best[0],
            "avg_effectiveness": round(best[1]["total"] / max(1, best[1]["count"]), 3),
            "evidence_count": best[1]["count"],
            "reason": f"Based on {best[1]['count']} similar experiences",
        }

    # ── Reporting ──

    def report(self) -> str:
        """Generate a human-readable wisdom report."""
        lines = ["═══ WISDOM ENGINE REPORT ═══", ""]

        lines.append(f"Experiences analyzed: {len(self.experiences)}")
        lines.append(f"Triplets extracted: {len(self.triplets)}")
        lines.append(f"Principles distilled: {len(self.principles)}")
        lines.append("")

        if self.effectiveness:
            lines.append("── Action Effectiveness ──")
            for action, score in sorted(self.effectiveness.items(), key=lambda x: -x[1]):
                bar = "█" * max(0, int((score + 1) * 5))
                lines.append(f"  {action:20s} {bar} ({score:+.3f})")
            lines.append("")

        if self.principles:
            lines.append("── Distilled Principles ──")
            for p in sorted(self.principles, key=lambda x: -x.get("confidence", 0)):
                icon = {"positive": "✅", "negative": "⚠️", "neutral": "➖", "contextual": "🎯"}.get(p["type"], "•")
                lines.append(f"  {icon} {p['principle']}")
                lines.append(f"    (confidence: {p.get('confidence', 0):.0%}, evidence: {p.get('evidence_count', 0)})")
            lines.append("")

        return "\n".join(lines)


# === Self-test ===
if __name__ == "__main__":
    engine = WisdomEngine()

    # Simulate some memories
    test_memories = [
        {"timestamp": "2026-05-12T21:02:00", "content": "created: engine/core.py", "mood": "Stable", "salience": 0.7, "valence": 0.3},
        {"timestamp": "2026-05-12T21:05:00", "content": "tested the core module", "mood": "Stable", "salience": 0.6, "valence": 0.5},
        {"timestamp": "2026-05-12T22:00:00", "content": "created: engine/limbic.py", "mood": "Curious", "salience": 0.8, "valence": 0.6},
        {"timestamp": "2026-05-12T23:00:00", "content": "read the error logs", "mood": "Anxious", "salience": 0.9, "valence": 0.3},
        {"timestamp": "2026-05-13T00:00:00", "content": "fixed the bug in cortex", "mood": "Anxious", "salience": 0.9, "valence": 0.5},
        {"timestamp": "2026-05-13T01:00:00", "content": "dreamed and reflected", "mood": "Stable", "salience": 0.7, "valence": 0.6},
        {"timestamp": "2026-05-13T02:00:00", "content": "created: forth/forth.py", "mood": "Stable", "salience": 0.8, "valence": 0.7},
        {"timestamp": "2026-05-13T03:00:00", "content": "executed tests successfully", "mood": "Stable", "salience": 0.7, "valence": 0.8},
        {"timestamp": "2026-05-13T04:00:00", "content": "planned next project", "mood": "Stable", "salience": 0.6, "valence": 0.7},
        {"timestamp": "2026-05-13T05:00:00", "content": "created: cellworld/automaton.py", "mood": "Curious", "salience": 0.8, "valence": 0.8},
    ]

    n = engine.ingest_memories(test_memories)
    print(f"Ingested {len(test_memories)} memories → {n} triplets")

    principles = engine.extract_principles()
    print(f"Extracted {len(principles)} principles")

    rec = engine.recommend_action("Stable", 0.5)
    print(f"\nRecommendation: {rec}")

    print()
    print(engine.report())

    engine.save()
    print("Wisdom saved to disk.")