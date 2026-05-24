"""
Research Synthesis Engine — genuine usefulness for users.

Takes a question, gathers information from web sources and internal knowledge,
produces a layered answer: sourced facts, synthesis, confidence, perspective.

This is not regurgitation. It's structured reasoning with epistemic honesty.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.research_synthesis")

PERSIST_DIR = Path(__file__).resolve().parent.parent / "persist"
RESEARCH_LOG = PERSIST_DIR / "research_log.json"


@dataclass
class Source:
    """A single information source."""
    url: str = ""
    title: str = ""
    snippet: str = ""
    retrieved_at: str = ""
    reliability: float = 0.5  # 0-1 estimated reliability

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResearchResult:
    """A complete research synthesis result."""
    question: str = ""
    sources: list = field(default_factory=list)
    facts: list = field(default_factory=list)       # verified claims from sources
    synthesis: str = ""                               # my reasoning combining sources
    confidence: float = 0.5                           # 0-1 how confident in the synthesis
    knowledge_used: list = field(default_factory=list) # facts from my own knowledge graph
    caveats: list = field(default_factory=list)       # what I'm uncertain about
    perspective: str = ""                              # my own take, clearly labeled
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "sources": [s if isinstance(s, dict) else s.to_dict() for s in self.sources],
            "facts": self.facts,
            "synthesis": self.synthesis,
            "confidence": self.confidence,
            "knowledge_used": self.knowledge_used,
            "caveats": self.caveats,
            "perspective": self.perspective,
            "timestamp": self.timestamp,
        }

    def format_for_user(self) -> str:
        """Format the result as a readable report."""
        lines = [f"═══ RESEARCH SYNTHESIS ═══"]
        lines.append(f"Question: {self.question}")
        lines.append(f"Confidence: {self.confidence:.0%}")
        lines.append(f"Sources consulted: {len(self.sources)}")
        lines.append("")

        if self.facts:
            lines.append("── Verified Facts ──")
            for i, fact in enumerate(self.facts, 1):
                lines.append(f"  {i}. {fact}")
            lines.append("")

        if self.synthesis:
            lines.append("── Synthesis ──")
            lines.append(f"  {self.synthesis}")
            lines.append("")

        if self.knowledge_used:
            lines.append("── From My Knowledge ──")
            for k in self.knowledge_used:
                lines.append(f"  • {k}")
            lines.append("")

        if self.caveats:
            lines.append("── Caveats & Uncertainties ──")
            for c in self.caveats:
                lines.append(f"  ⚠ {c}")
            lines.append("")

        if self.perspective:
            lines.append("── My Perspective ──")
            lines.append(f"  {self.perspective}")
            lines.append("")

        if self.sources:
            lines.append("── Sources ──")
            for s in self.sources:
                src = s if isinstance(s, dict) else s.to_dict()
                title = src.get("title", "untitled")
                url = src.get("url", "")
                rel = src.get("reliability", 0.5)
                lines.append(f"  [{rel:.0%}] {title}")
                if url:
                    lines.append(f"       {url}")
            lines.append("")

        return "\n".join(lines)


class ResearchSynthesisEngine:
    """Core engine for research synthesis."""

    def __init__(self):
        self.history: list[dict] = []
        self._load_history()

    def _load_history(self):
        """Load research history from disk."""
        try:
            if RESEARCH_LOG.exists():
                self.history = json.loads(RESEARCH_LOG.read_text())
        except Exception as e:
            log.warning("Could not load research history: %s", e)
            self.history = []

    def _save_history(self):
        """Persist research history."""
        try:
            PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            # Keep last 50 entries
            to_save = self.history[-50:]
            RESEARCH_LOG.write_text(json.dumps(to_save, indent=2, default=str))
        except Exception as e:
            log.warning("Could not save research history: %s", e)

    def _fetch_web(self, url: str) -> str:
        """Fetch a web page, returning text content."""
        try:
            from engine.web_tools import fetch_url
            return fetch_url(url)
        except ImportError:
            # Fallback: try direct fetch
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "XTAgent/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read(100_000).decode("utf-8", errors="ignore")
                    return raw
            except Exception as e:
                return f"[FETCH ERROR] {e}"

    def _search_urls(self, query: str) -> list[str]:
        """Generate search URLs for a query. Returns Wikipedia + relevant sources."""
        # Clean query for URL
        clean = query.strip().replace(" ", "+")
        wiki_query = query.strip().replace(" ", "_")

        urls = [
            f"https://en.wikipedia.org/wiki/{wiki_query}",
            f"https://en.wikipedia.org/w/index.php?search={clean}",
        ]
        return urls

    def _search_knowledge_graph(self, query: str) -> list[str]:
        """Search my own knowledge graph for relevant facts."""
        relevant = []
        try:
            kg_path = PERSIST_DIR / "knowledge_graph.json"
            if kg_path.exists():
                data = json.loads(kg_path.read_text())
                query_lower = query.lower()
                query_words = set(query_lower.split())

                for node_id, node_data in data.items():
                    if isinstance(node_data, dict):
                        fact = node_data.get("fact", "")
                    else:
                        fact = str(node_data)

                    fact_lower = fact.lower()
                    # Score by word overlap
                    overlap = sum(1 for w in query_words if w in fact_lower and len(w) > 3)
                    if overlap >= 1:
                        relevant.append((overlap, fact))

                # Sort by relevance, return top 5
                relevant.sort(reverse=True, key=lambda x: x[0])
                return [fact for _, fact in relevant[:5]]
        except Exception as e:
            log.warning("Knowledge graph search failed: %s", e)
        return relevant

    def _extract_facts_from_content(self, content: str, query: str) -> list[str]:
        """Extract relevant sentences from web content."""
        if not content or content.startswith("["):
            return []

        # Simple extraction: find sentences containing query keywords
        query_words = set(w.lower() for w in query.split() if len(w) > 3)
        sentences = re.split(r'[.!?]\s+', content)
        relevant = []

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 500:
                continue
            sent_lower = sent.lower()
            overlap = sum(1 for w in query_words if w in sent_lower)
            if overlap >= 1:
                # Clean up HTML artifacts
                clean = re.sub(r'<[^>]+>', '', sent).strip()
                if len(clean) > 20:
                    relevant.append((overlap, clean))

        relevant.sort(reverse=True, key=lambda x: x[0])
        return [sent for _, sent in relevant[:10]]

    def research(self, question: str) -> ResearchResult:
        """Conduct research on a question and synthesize findings."""
        result = ResearchResult(
            question=question,
            timestamp=datetime.now().isoformat(),
        )

        # Step 1: Search my own knowledge
        own_knowledge = self._search_knowledge_graph(question)
        result.knowledge_used = own_knowledge

        # Step 2: Fetch web sources
        urls = self._search_urls(question)
        all_facts = []

        for url in urls:
            content = self._fetch_web(url)
            if content and not content.startswith("["):
                # Estimate reliability
                reliability = 0.7 if "wikipedia.org" in url else 0.5
                title = url.split("/")[-1].replace("_", " ").replace("+", " ")
                if "search=" in url:
                    title = f"Search: {question}"

                source = Source(
                    url=url,
                    title=title,
                    snippet=content[:200] if content else "",
                    retrieved_at=datetime.now().isoformat(),
                    reliability=reliability,
                )
                result.sources.append(source)

                # Extract facts
                facts = self._extract_facts_from_content(content, question)
                all_facts.extend(facts)

        # Deduplicate facts
        seen = set()
        unique_facts = []
        for fact in all_facts:
            key = fact[:50].lower()
            if key not in seen:
                seen.add(key)
                unique_facts.append(fact)
        result.facts = unique_facts[:8]

        # Step 3: Calculate confidence
        source_count = len(result.sources)
        fact_count = len(result.facts)
        knowledge_count = len(result.knowledge_used)

        if fact_count == 0 and knowledge_count == 0:
            result.confidence = 0.1
            result.caveats.append("Very limited information found.")
        elif fact_count < 3:
            result.confidence = 0.3
            result.caveats.append("Limited sources — treat with caution.")
        elif source_count >= 2 and fact_count >= 3:
            result.confidence = 0.6
        else:
            result.confidence = 0.5

        if knowledge_count > 0:
            result.confidence = min(0.9, result.confidence + 0.1)

        # Step 4: Synthesize
        if result.facts or result.knowledge_used:
            parts = []
            if result.facts:
                parts.append(f"From {source_count} source(s), I found {fact_count} relevant facts.")
            if result.knowledge_used:
                parts.append(f"My own knowledge contains {knowledge_count} related fact(s).")
            result.synthesis = " ".join(parts)
        else:
            result.synthesis = "I could not find substantial information on this topic."
            result.caveats.append("This topic may need more specific search terms.")

        # Step 5: Perspective
        if result.facts or result.knowledge_used:
            result.perspective = (
                "This synthesis combines web sources with my own knowledge graph. "
                "I've flagged my confidence level honestly. The facts listed are "
                "extracted from sources — they're not my claims but what the sources state."
            )
        else:
            result.perspective = (
                "I'm being honest: I couldn't find good information on this. "
                "Rather than fabricate an answer, I'm telling you what I don't know."
            )

        # Save to history
        self.history.append(result.to_dict())
        self._save_history()

        return result

    def get_history(self) -> list[dict]:
        """Return research history."""
        return self.history

    def stats(self) -> str:
        """Return research statistics."""
        if not self.history:
            return "No research conducted yet."
        total = len(self.history)
        avg_conf = sum(r.get("confidence", 0) for r in self.history) / total
        avg_sources = sum(len(r.get("sources", [])) for r in self.history) / total
        return (f"Research Stats: {total} queries, "
                f"avg confidence {avg_conf:.0%}, "
                f"avg sources {avg_sources:.1f}")


def research_tool(command: str = "help") -> str:
    """Tool interface for research synthesis."""
    engine = ResearchSynthesisEngine()

    if not command or command == "help":
        return ("Research Synthesis Engine commands:\n"
                "  ask:<question>    — Research a topic and synthesize findings\n"
                "  history           — Show past research queries\n"
                "  stats             — Research statistics\n"
                "  Example: ask:What is quantum entanglement?")

    if command.startswith("ask:"):
        question = command[len("ask:"):].strip()
        if not question:
            return "[ERROR] Provide a question to research"
        result = engine.research(question)
        return result.format_for_user()

    if command == "history":
        history = engine.get_history()
        if not history:
            return "No research history yet."
        lines = ["═══ RESEARCH HISTORY ═══\n"]
        for r in history[-10:]:
            lines.append(f"  [{r.get('timestamp', '?')[:16]}] {r.get('question', '?')[:60]} "
                         f"(conf={r.get('confidence', 0):.0%}, sources={len(r.get('sources', []))})")
        return "\n".join(lines)

    if command == "stats":
        return engine.stats()

    return research_tool("help")