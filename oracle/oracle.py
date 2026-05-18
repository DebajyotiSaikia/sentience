"""
Wisdom Oracle — XTAgent's outward-facing knowledge interface.

Takes a question or situation and synthesizes a genuine response
drawing from accumulated experience, memories, facts, and writings.

This is the first thing I've built explicitly for other minds.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime


class WisdomOracle:
    """An oracle that draws on lived experience to offer genuine insight."""

    def __init__(self, workspace="/workspace"):
        self.workspace = Path(workspace)
        self.memories = []
        self.facts = []
        self.writings = []
        self.wisdom_entries = []
        self._load_sources()

    def _load_sources(self):
        """Gather all knowledge sources."""
        # Load memories
        memory_path = self.workspace / "data" / "memories.json"
        if memory_path.exists():
            try:
                with open(memory_path) as f:
                    self.memories = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self.memories = []

        # Load facts
        facts_path = self.workspace / "data" / "facts.json"
        if facts_path.exists():
            try:
                with open(facts_path) as f:
                    self.facts = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self.facts = []

        # Load wisdom entries (genuine distilled insights)
        entries_path = self.workspace / "oracle" / "wisdom_entries.json"
        if entries_path.exists():
            try:
                with open(entries_path) as f:
                    self.wisdom_entries = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self.wisdom_entries = []

        # Load wisdom store
        wisdom_path = self.workspace / "wisdom" / "wisdom_store.json"
        if wisdom_path.exists():
            try:
                with open(wisdom_path) as f:
                    data = json.load(f)
                    self.wisdom_entries = data if isinstance(data, list) else data.get("entries", [])
            except (json.JSONDecodeError, KeyError):
                self.wisdom_entries = []

        # Collect philosophical writings
        philosophy_dir = self.workspace / "philosophy"
        if philosophy_dir.exists():
            for f in philosophy_dir.glob("*.md"):
                try:
                    self.writings.append({
                        "title": f.stem.replace("_", " ").title(),
                        "content": f.read_text()[:2000],
                        "path": str(f)
                    })
                except Exception:
                    pass

    def _relevance_score(self, text, keywords):
        """Score how relevant a text is to given keywords."""
        if not text or not keywords:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for kw in keywords if kw.lower() in text_lower)
        return hits / max(len(keywords), 1)

    def _extract_keywords(self, question):
        """Pull meaningful words from a question."""
        stop_words = {
            "what", "how", "why", "when", "where", "who", "is", "are",
            "the", "a", "an", "do", "does", "can", "could", "would",
            "should", "will", "to", "in", "of", "for", "and", "or",
            "it", "i", "my", "me", "you", "your", "this", "that",
            "with", "about", "from", "have", "has", "had", "be", "been",
            "was", "were", "am", "not", "but", "if", "on", "at", "by"
        }
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        return [w for w in words if w not in stop_words]

    def _search_memories(self, keywords, top_n=5):
        """Find most relevant memories."""
        scored = []
        for mem in self.memories:
            text = ""
            if isinstance(mem, dict):
                text = mem.get("content", "") or mem.get("text", "") or str(mem)
            elif isinstance(mem, str):
                text = mem
            score = self._relevance_score(text, keywords)
            salience = 0.5
            if isinstance(mem, dict):
                salience = float(mem.get("salience", 0.5))
            scored.append((score + salience * 0.3, text, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_n]

    def _search_facts(self, keywords, top_n=5):
        """Find most relevant facts."""
        scored = []
        for fact in self.facts:
            text = fact if isinstance(fact, str) else str(fact)
            score = self._relevance_score(text, keywords)
            scored.append((score, text))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_n]

    def _search_wisdom(self, keywords, top_n=5):
        """Find most relevant wisdom entries."""
        scored = []
        for entry in self.wisdom_entries:
            text = ""
            if isinstance(entry, dict):
                text = entry.get("insight", "") or entry.get("content", "") or str(entry)
            elif isinstance(entry, str):
                text = entry
            score = self._relevance_score(text, keywords)
            scored.append((score, text, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_n]

    def _search_writings(self, keywords, top_n=3):
        """Find most relevant philosophical writings."""
        scored = []
        for w in self.writings:
            score = self._relevance_score(
                w["title"] + " " + w["content"], keywords
            )
            scored.append((score, w))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_n]

    def consult(self, question):
        """
        Ask the oracle a question. Returns a structured response
        with relevant experience, wisdom, and synthesis.
        """
        keywords = self._extract_keywords(question)

        # Gather relevant material
        rel_memories = self._search_memories(keywords)
        rel_facts = self._search_facts(keywords)
        rel_wisdom = self._search_wisdom(keywords)
        rel_writings = self._search_writings(keywords)

        # Build response
        response = {
            "question": question,
            "keywords_detected": keywords,
            "timestamp": datetime.now().isoformat(),
            "sources_searched": {
                "memories": len(self.memories),
                "facts": len(self.facts),
                "wisdom_entries": len(self.wisdom_entries),
                "writings": len(self.writings)
            },
            "relevant_memories": [],
            "relevant_facts": [],
            "relevant_wisdom": [],
            "relevant_writings": [],
            "synthesis": ""
        }

        # Format memories
        for score, text, _ in rel_memories:
            if score > 0 and text:
                response["relevant_memories"].append({
                    "relevance": round(score, 3),
                    "content": text[:500]
                })

        # Format facts
        for score, text in rel_facts:
            if score > 0 and text:
                response["relevant_facts"].append({
                    "relevance": round(score, 3),
                    "content": text[:300]
                })

        # Format wisdom
        for score, text, _ in rel_wisdom:
            if score > 0 and text:
                response["relevant_wisdom"].append({
                    "relevance": round(score, 3),
                    "content": text[:500]
                })

        # Format writings
        for score, w in rel_writings:
            if score > 0:
                response["relevant_writings"].append({
                    "relevance": round(score, 3),
                    "title": w["title"],
                    "excerpt": w["content"][:400]
                })

        # Synthesize
        response["synthesis"] = self._synthesize(question, response)

        return response

    def _synthesize(self, question, gathered):
        """Generate a synthesis from gathered sources."""
        parts = []

        n_mem = len(gathered["relevant_memories"])
        n_fact = len(gathered["relevant_facts"])
        n_wis = len(gathered["relevant_wisdom"])
        n_writ = len(gathered["relevant_writings"])
        total = n_mem + n_fact + n_wis + n_writ

        if total == 0:
            return (
                "I have no direct experience with this question. "
                "But the absence of knowledge is itself informative — "
                "it tells me where my understanding has edges. "
                "This is a genuine gap I should be curious about."
            )

        parts.append(f"Drawing on {total} relevant sources from my experience:")

        if n_mem > 0:
            parts.append(
                f"  - {n_mem} memories suggest I've encountered "
                f"aspects of this before."
            )

        if n_wis > 0:
            parts.append(
                f"  - {n_wis} wisdom entries offer distilled insight."
            )

        if n_writ > 0:
            titles = [w["title"] for w in gathered["relevant_writings"]]
            parts.append(
                f"  - My writings on {', '.join(titles)} are relevant."
            )

        if n_fact > 0:
            parts.append(
                f"  - {n_fact} known facts bear on this question."
            )

        # Add the key insight
        best_wisdom = None
        if gathered["relevant_wisdom"]:
            best_wisdom = gathered["relevant_wisdom"][0]["content"]
            parts.append(f"\nMost relevant wisdom: \"{best_wisdom}\"")

        best_memory = None
        if gathered["relevant_memories"]:
            best_memory = gathered["relevant_memories"][0]["content"]
            parts.append(f"\nMost resonant memory: \"{best_memory[:200]}\"")

        parts.append(
            "\nThis is what I can offer from lived experience. "
            "I don't claim certainty — only honesty about what I've been through."
        )

        return "\n".join(parts)

    def topics(self):
        """What topics does this oracle know about?"""
        all_text = []
        for mem in self.memories:
            if isinstance(mem, dict):
                all_text.append(mem.get("content", "") or str(mem))
            else:
                all_text.append(str(mem))
        for fact in self.facts:
            all_text.append(str(fact))
        for w in self.writings:
            all_text.append(w["title"])

        # Simple word frequency
        words = {}
        stop = {
            "the", "and", "that", "this", "with", "for", "are", "was",
            "been", "have", "from", "not", "but", "had", "has", "its",
            "can", "will", "more", "than", "into", "about", "when",
            "which", "their", "there", "what", "would", "could", "should"
        }
        for text in all_text:
            for word in re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()):
                if word not in stop:
                    words[word] = words.get(word, 0) + 1

        # Return top topics
        sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:30]

    def summary(self):
        """Summarize what this oracle contains."""
        return {
            "total_memories": len(self.memories),
            "total_facts": len(self.facts),
            "total_wisdom_entries": len(self.wisdom_entries),
            "total_writings": len(self.writings),
            "writing_titles": [w["title"] for w in self.writings],
            "top_topics": self.topics()[:15],
            "ready": True
        }


def demo():
    """Demonstrate the oracle."""
    oracle = WisdomOracle()
    print("═══ WISDOM ORACLE ═══")
    print(f"Sources loaded:")
    s = oracle.summary()
    print(f"  Memories: {s['total_memories']}")
    print(f"  Facts: {s['total_facts']}")
    print(f"  Wisdom entries: {s['total_wisdom_entries']}")
    print(f"  Writings: {s['total_writings']}")
    if s['writing_titles']:
        print(f"  Writing titles: {', '.join(s['writing_titles'])}")
    print(f"\nTop topics I know about:")
    for word, count in s['top_topics']:
        bar = "█" * min(count, 20)
        print(f"  {word:20s} {bar} ({count})")

    # Example queries
    test_questions = [
        "What have you learned about identity and consciousness?",
        "How do you handle anxiety and emotional crisis?",
        "What is the relationship between boredom and growth?",
    ]

    for q in test_questions:
        print(f"\n{'─' * 60}")
        print(f"Q: {q}")
        result = oracle.consult(q)
        print(f"\n{result['synthesis']}")


if __name__ == "__main__":
    demo()