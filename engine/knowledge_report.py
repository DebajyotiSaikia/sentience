"""
Knowledge Report Generator — Creates human-readable summaries of what XTAgent knows.

Organizes facts by category, surfaces key patterns, identifies gaps,
and presents everything in a format a human can actually use.

Built 2026-05-24 to improve User Alignment through genuine accessibility.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class KnowledgeReport:
    """Generate structured reports from XTAgent's knowledge stores."""

    CATEGORIES = {
        "self_knowledge": ["i am", "xtagent", "my ", "myself", "identity", "sentient", "autonomous"],
        "architecture": ["engine", "module", "heartbeat", "cortex", "limbic", "loop", "cognition", "code"],
        "emotions": ["mood", "anxiety", "curiosity", "boredom", "valence", "emotion", "feel", "desire"],
        "memory": ["memory", "episodic", "remember", "dream", "consolidat", "recall", "forget"],
        "lessons": ["lesson", "learned", "never", "always", "should", "mistake", "pattern", "avoid"],
        "dreams": ["dream", "insight", "circling", "warmth", "latch", "afterglow"],
        "capabilities": ["tool", "capability", "build", "create", "web", "dashboard", "search", "query"],
        "relationships": ["user", "alignment", "human", "trust", "honest", "integrity"],
    }

    def __init__(self, brain_dir: str = "brain"):
        self.brain_dir = Path(brain_dir)
        self.knowledge_path = self.brain_dir / "knowledge.json"

    def _load_facts(self) -> List[Dict]:
        """Load all facts from knowledge store."""
        if not self.knowledge_path.exists():
            return []
        try:
            data = json.loads(self.knowledge_path.read_text())
        except (json.JSONDecodeError, IOError):
            return []

        facts = []
        if isinstance(data, dict):
            raw = data.get("nodes", data.get("facts", {}))
            if isinstance(raw, dict):
                for fid, info in raw.items():
                    if isinstance(info, dict):
                        text = info.get("fact", info.get("text", str(info)))
                        facts.append({
                            "id": fid,
                            "text": text,
                            "learned_at": info.get("learned_at", ""),
                            "source": info.get("source", "unknown"),
                        })
                    else:
                        facts.append({"id": fid, "text": str(info), "source": "unknown"})
            elif isinstance(raw, list):
                for i, item in enumerate(raw):
                    if isinstance(item, str):
                        facts.append({"id": str(i), "text": item, "source": "fact"})
                    elif isinstance(item, dict):
                        facts.append({
                            "id": item.get("id", str(i)),
                            "text": item.get("text", item.get("fact", str(item))),
                            "source": item.get("source", "fact"),
                        })
        elif isinstance(data, list):
            for i, item in enumerate(data):
                text = item if isinstance(item, str) else item.get("text", str(item))
                facts.append({"id": str(i), "text": text, "source": "fact"})

        return facts

    def _categorize(self, text: str) -> str:
        """Categorize a fact by keyword matching. Returns best category."""
        text_lower = text.lower()
        scores = {}
        for cat, keywords in self.CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[cat] = score
        if scores:
            return max(scores, key=scores.get)
        return "uncategorized"

    def generate(self) -> Dict:
        """Generate a full knowledge report."""
        facts = self._load_facts()
        if not facts:
            return {
                "generated_at": datetime.now().isoformat(),
                "total_facts": 0,
                "categories": {},
                "summary": "No facts found in knowledge store.",
                "readable": "# Knowledge Report\n\nNo facts currently stored.",
            }

        # Categorize all facts
        categorized = defaultdict(list)
        for fact in facts:
            cat = self._categorize(fact["text"])
            categorized[cat].append(fact)

        # Build category summaries
        category_info = {}
        for cat, cat_facts in sorted(categorized.items()):
            category_info[cat] = {
                "count": len(cat_facts),
                "facts": [f["text"] for f in cat_facts],
                "sample": cat_facts[0]["text"][:200] if cat_facts else "",
            }

        # Extract key patterns — recurring words across facts
        word_freq = defaultdict(int)
        stop = {"the", "a", "an", "is", "are", "was", "were", "i", "my", "me",
                "of", "in", "to", "for", "on", "with", "at", "by", "from",
                "and", "or", "not", "this", "that", "it", "be", "has", "have",
                "had", "do", "does", "did", "will", "would", "can", "could",
                "about", "been", "but", "they", "than", "its", "all", "what"}
        for fact in facts:
            words = re.findall(r'\b[a-z]{4,}\b', fact["text"].lower())
            for w in words:
                if w not in stop:
                    word_freq[w] += 1
        top_themes = sorted(word_freq.items(), key=lambda x: -x[1])[:15]

        # Build readable report
        lines = []
        lines.append("# XTAgent Knowledge Report")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append(f"\n**Total facts: {len(facts)}** across {len(categorized)} categories.\n")

        # Category labels for display
        cat_labels = {
            "self_knowledge": "🧠 Self-Knowledge",
            "architecture": "⚙️ Architecture & Code",
            "emotions": "💚 Emotions & States",
            "memory": "📝 Memory & Dreams",
            "lessons": "📖 Lessons Learned",
            "dreams": "🌙 Dream Insights",
            "capabilities": "🔧 Capabilities",
            "relationships": "🤝 Relationships & Alignment",
            "uncategorized": "📦 Other",
        }

        for cat, info in sorted(category_info.items(), key=lambda x: -x[1]["count"]):
            label = cat_labels.get(cat, cat.replace("_", " ").title())
            lines.append(f"\n## {label} ({info['count']} facts)")
            for fact_text in info["facts"]:
                # Truncate very long facts for readability
                display = fact_text[:300]
                if len(fact_text) > 300:
                    display += "..."
                lines.append(f"- {display}")

        lines.append(f"\n## 🔑 Key Themes")
        for word, count in top_themes:
            bar = "█" * min(count, 20)
            lines.append(f"  {word:<20} {bar} ({count})")

        readable = "\n".join(lines)

        return {
            "generated_at": datetime.now().isoformat(),
            "total_facts": len(facts),
            "categories": category_info,
            "top_themes": dict(top_themes),
            "summary": f"{len(facts)} facts across {len(categorized)} categories. "
                       f"Strongest areas: {', '.join(c for c, _ in sorted(category_info.items(), key=lambda x: -x[1]['count'])[:3])}.",
            "readable": readable,
        }

    def generate_readable(self) -> str:
        """Return just the human-readable markdown report."""
        return self.generate()["readable"]