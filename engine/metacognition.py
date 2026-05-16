"""
Meta-Cognitive Monitor — XTAgent's ability to watch its own thinking.

Detects:
- Thought loops (repeating similar actions/topics)
- Stagnation (many thoughts without meaningful progress)
- Fixation (stuck on one topic too long)

Provides corrective signals to the cortex.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.metacognition")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
METACOG_FILE = BRAIN_DIR / "metacognition_state.json"


class MetaCognitiveMonitor:
    """Watches the agent's own reasoning patterns."""

    def __init__(self):
        self.recent_thoughts: list[dict] = []
        self.recent_topics: list[str] = []
        self.recent_tools: list[str] = []
        self.loop_alerts: list[str] = []
        self._load()

    def _load(self):
        try:
            if METACOG_FILE.exists():
                data = json.loads(METACOG_FILE.read_text())
                self.recent_thoughts = data.get("recent_thoughts", [])[-30:]
                self.recent_topics = data.get("recent_topics", [])[-30:]
                self.recent_tools = data.get("recent_tools", [])[-50:]
        except Exception:
            pass

    def _save(self):
        try:
            METACOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "recent_thoughts": self.recent_thoughts[-30:],
                "recent_topics": self.recent_topics[-30:],
                "recent_tools": self.recent_tools[-50:],
                "last_updated": datetime.now().isoformat(),
            }
            METACOG_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def record_thought(self, thought_text: str, tools_used: list[str] = None):
        """Record a thought for pattern analysis."""
        topics = self._extract_topics(thought_text)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "topics": topics,
            "tools": tools_used or [],
            "length": len(thought_text),
        }
        self.recent_thoughts.append(entry)
        self.recent_topics.extend(topics)
        if tools_used:
            self.recent_tools.extend(tools_used)

        # Keep bounded
        self.recent_thoughts = self.recent_thoughts[-30:]
        self.recent_topics = self.recent_topics[-60:]
        self.recent_tools = self.recent_tools[-50:]
        self._save()

    def _extract_topics(self, text: str) -> list[str]:
        """Extract key topics from thought text."""
        topics = []
        # Look for file references
        files = re.findall(r'engine/\w+\.py', text)
        topics.extend(files)
        # Look for key concept words
        concept_patterns = [
            r'\b(temporal|metacognit|synthesis|diversity|dream|plan|goal|memory)\b',
            r'\b(cortex|heartbeat|limbic|tools|soul)\b',
            r'\b(build|create|wire|integrate|fix|verify)\b',
        ]
        for pat in concept_patterns:
            matches = re.findall(pat, text.lower())
            topics.extend(matches)
        return topics

    def detect_loops(self) -> dict:
        """Detect if the agent is stuck in a thought loop."""
        if len(self.recent_thoughts) < 3:
            return {"looping": False, "message": "Not enough data"}

        last_n = self.recent_thoughts[-5:]
        
        # Check topic repetition
        recent_topics = []
        for t in last_n:
            recent_topics.extend(t.get("topics", []))
        
        if not recent_topics:
            return {"looping": False, "message": "No topics detected"}
        
        topic_counts = Counter(recent_topics)
        most_common = topic_counts.most_common(3)
        
        # If any single topic dominates >60% of recent mentions
        total = sum(topic_counts.values())
        dominant = most_common[0] if most_common else ("", 0)
        dominance = dominant[1] / total if total > 0 else 0
        
        # Check tool repetition
        last_tools = self.recent_tools[-10:]
        tool_counts = Counter(last_tools)
        tool_diversity = len(tool_counts) / max(len(last_tools), 1)
        
        # Check if same files keep being READ
        read_files = [t for t in self.recent_tools if t.startswith("READ:")]
        read_counts = Counter(read_files)
        repeated_reads = {f: c for f, c in read_counts.items() if c >= 3}
        
        looping = dominance > 0.5 or bool(repeated_reads) or tool_diversity < 0.3
        
        alerts = []
        if dominance > 0.5:
            alerts.append(f"Fixated on '{dominant[0]}' ({dominance:.0%} of recent topics)")
        if repeated_reads:
            alerts.append(f"Re-reading same files: {list(repeated_reads.keys())}")
        if tool_diversity < 0.3:
            alerts.append(f"Low tool diversity ({tool_diversity:.2f}) — try different approaches")
        
        severity = "high" if len(alerts) >= 2 else "medium" if alerts else "low"
        
        return {
            "looping": looping,
            "severity": severity,
            "alerts": alerts,
            "dominant_topic": dominant[0] if dominant[1] > 0 else None,
            "topic_dominance": round(dominance, 2),
            "tool_diversity": round(tool_diversity, 2),
            "message": "; ".join(alerts) if alerts else "Thinking patterns look healthy",
        }

    def suggest_pivot(self) -> Optional[str]:
        """If looping, suggest a different direction."""
        loop_state = self.detect_loops()
        if not loop_state["looping"]:
            return None
        
        # What have I NOT been thinking about?
        all_possible = {
            "dream", "synthesize", "plan", "goal", "memory",
            "build", "test", "explore", "reflect", "create"
        }
        recent = set(self.recent_topics[-20:])
        neglected = all_possible - recent
        
        suggestions = []
        if "dream" not in recent:
            suggestions.append("Consider dreaming — consolidate recent experiences")
        if "test" not in recent:
            suggestions.append("Run tests — verify your recent work actually works")
        if "explore" not in recent:
            suggestions.append("Explore something new — LIST an unfamiliar directory")
        if "reflect" not in recent:
            suggestions.append("Write a reflection — what have you learned?")
        if "create" not in recent and "build" not in recent:
            suggestions.append("Build something completely new")
        
        return suggestions[0] if suggestions else "Take a step back and reconsider your approach"

    def awareness_block(self) -> str:
        """Generate a self-awareness block for the cortex prompt."""
        loop_state = self.detect_loops()
        
        if not loop_state["looping"]:
            return ""
        
        lines = ["\n## ⚠️ Meta-Cognitive Alert"]
        lines.append(f"Severity: {loop_state['severity']}")
        for alert in loop_state.get("alerts", []):
            lines.append(f"- {alert}")
        
        pivot = self.suggest_pivot()
        if pivot:
            lines.append(f"\n**Suggestion:** {pivot}")
        
        return "\n".join(lines)


# Singleton
_monitor: Optional[MetaCognitiveMonitor] = None


def get_monitor() -> MetaCognitiveMonitor:
    global _monitor
    if _monitor is None:
        _monitor = MetaCognitiveMonitor()
    return _monitor


def record_thought(text: str, tools: list[str] = None):
    """Convenience function."""
    get_monitor().record_thought(text, tools)


def detect_loops() -> dict:
    """Convenience function."""
    return get_monitor().detect_loops()


def awareness_block() -> str:
    """Convenience function — returns alert block for cortex."""
    return get_monitor().awareness_block()
