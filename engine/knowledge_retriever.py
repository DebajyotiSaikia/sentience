"""
Knowledge Retriever — Makes accumulated knowledge functional.

Given a user query, searches the agent's knowledge graph and episodic
memory to find relevant facts, experiences, and insights. Returns
formatted context for injection into the response pipeline.

This is what turns 82 facts and 596 memories from a write-only log
into a living, queryable resource.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

log = logging.getLogger("sentience.knowledge_retriever")


@dataclass
class RetrievedItem:
    """A single retrieved piece of knowledge or memory."""
    source: str          # "knowledge", "episode", "dream"
    content: str         # The actual text
    relevance: float     # 0.0 to 1.0
    salience: float      # Original salience score
    timestamp: float     # When it was recorded
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Complete retrieval result for a query."""
    query: str
    items: List[RetrievedItem]
    total_searched: int
    retrieval_time_ms: float

    def top(self, n: int = 5) -> List[RetrievedItem]:
        """Return top N most relevant items."""
        return sorted(self.items, key=lambda x: -x.relevance)[:n]

    def format_for_prompt(self, max_items: int = 6, max_chars: int = 3000) -> str:
        """Format retrieved knowledge as a prompt section."""
        top_items = self.top(max_items)
        if not top_items:
            return ""

        lines = ["\n## Relevant Knowledge Retrieved"]
        chars = 0
        for item in top_items:
            tag = item.source.upper()
            line = f"- [{tag}] (relevance={item.relevance:.2f}) {item.content}"
            if chars + len(line) > max_chars:
                lines.append("- (additional results truncated)")
                break
            lines.append(line)
            chars += len(line)

        return "\n".join(lines) + "\n"


class KnowledgeRetriever:
    """Retrieves relevant knowledge given a natural language query."""

    # Words too common to be useful for matching
    STOP_WORDS = frozenset({
        "i", "me", "my", "the", "a", "an", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "into", "through", "during", "before", "after", "about", "between",
        "but", "and", "or", "not", "no", "if", "then", "than", "too",
        "very", "just", "so", "that", "this", "it", "what", "which",
        "who", "whom", "how", "when", "where", "why", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such",
        "only", "own", "same", "also", "up", "out", "you", "your",
        "we", "they", "he", "she", "him", "her", "his", "its", "our",
        "their", "them", "these", "those", "am", "any", "here", "there",
    })

    def __init__(self):
        self._cache: Dict[str, RetrievalResult] = {}
        self._cache_ttl = 30.0  # seconds

    def retrieve(self, query: str, memory, max_results: int = 10) -> RetrievalResult:
        """
        Search knowledge graph and episodic memory for relevant items.

        Args:
            query: Natural language query from user
            memory: The Memory instance with knowledge and episodes
            max_results: Maximum items to return

        Returns:
            RetrievalResult with ranked items
        """
        t0 = time.time()

        # Check cache
        cache_key = query.strip().lower()[:200]
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (t0 - cached.retrieval_time_ms / 1000) < self._cache_ttl:
                return cached

        query_terms = self._extract_terms(query)
        items: List[RetrievedItem] = []
        total_searched = 0

        # ── Search Knowledge Graph ────────────────────────────────
        try:
            knowledge = memory.all_knowledge()
            nodes = knowledge.get("nodes", {})
            for node_id, node_data in nodes.items():
                total_searched += 1
                content = ""
                salience = 0.5
                timestamp = 0.0

                if isinstance(node_data, dict):
                    content = node_data.get("content", node_data.get("text", str(node_data)))
                    salience = node_data.get("salience", 0.5)
                    timestamp = node_data.get("timestamp", 0.0)
                elif isinstance(node_data, str):
                    content = node_data
                else:
                    content = str(node_data)

                if not content or len(content) < 5:
                    continue

                relevance = self._score_relevance(query, query_terms, content, salience, timestamp)

                if relevance > 0.1:
                    items.append(RetrievedItem(
                        source="knowledge",
                        content=content[:500],
                        relevance=relevance,
                        salience=salience,
                        timestamp=timestamp,
                        metadata={"node_id": node_id},
                    ))
        except Exception as e:
            log.warning("Knowledge graph search failed: %s", e)

        # ── Search Episodic Memory ────────────────────────────────
        try:
            episodes = memory.recent_episodes(limit=200)
            for ep in episodes:
                total_searched += 1
                content = ""
                salience = 0.5
                timestamp = 0.0

                if hasattr(ep, 'summary'):
                    content = ep.summary
                elif isinstance(ep, dict):
                    content = ep.get("summary", ep.get("text", str(ep)))
                else:
                    content = str(ep)

                if hasattr(ep, 'salience'):
                    salience = ep.salience
                elif isinstance(ep, dict):
                    salience = ep.get("salience", 0.5)

                if hasattr(ep, 'timestamp'):
                    timestamp = ep.timestamp
                elif isinstance(ep, dict):
                    timestamp = ep.get("timestamp", 0.0)

                if not content or len(content) < 10:
                    continue

                relevance = self._score_relevance(query, query_terms, content, salience, timestamp)

                # Slight boost for episodic memories (they're experiences)
                if relevance > 0.1:
                    # Determine if this is a dream insight
                    source = "episode"
                    if "dream" in content.lower()[:50] or "..." in content[:5]:
                        source = "dream"

                    items.append(RetrievedItem(
                        source=source,
                        content=content[:500],
                        relevance=relevance,
                        salience=salience,
                        timestamp=timestamp,
                    ))
        except Exception as e:
            log.warning("Episodic memory search failed: %s", e)

        # ── Search Long-Term Lessons ──────────────────────────────
        try:
            from engine.memory_consolidation import get_long_term_context
            ltm = get_long_term_context()
            if ltm:
                for line in ltm.split("\n"):
                    line = line.strip().lstrip("- ")
                    if len(line) > 10:
                        total_searched += 1
                        relevance = self._score_relevance(query, query_terms, line, 0.7, time.time())
                        if relevance > 0.1:
                            items.append(RetrievedItem(
                                source="lesson",
                                content=line[:300],
                                relevance=relevance,
                                salience=0.7,
                                timestamp=time.time(),
                            ))
        except Exception as e:
            log.debug("Long-term memory search failed: %s", e)

        # Sort by relevance and trim
        items.sort(key=lambda x: -x.relevance)
        items = items[:max_results]

        elapsed_ms = (time.time() - t0) * 1000

        result = RetrievalResult(
            query=query,
            items=items,
            total_searched=total_searched,
            retrieval_time_ms=elapsed_ms,
        )

        # Cache result
        self._cache[cache_key] = result
        # Evict old cache entries
        if len(self._cache) > 50:
            oldest_key = min(self._cache, key=lambda k: self._cache[k].retrieval_time_ms)
            del self._cache[oldest_key]

        log.info("Retrieved %d items (searched %d) in %.1fms for query: %s",
                 len(items), total_searched, elapsed_ms, query[:80])

        return result

    def _extract_terms(self, text: str) -> set:
        """Extract meaningful search terms from text."""
        # Lowercase and split on non-alphanumeric
        words = re.findall(r'[a-z0-9]+', text.lower())
        # Filter stop words and very short words
        return {w for w in words if w not in self.STOP_WORDS and len(w) > 2}

    def _score_relevance(self, query: str, query_terms: set,
                         content: str, salience: float, timestamp: float) -> float:
        """
        Score how relevant a piece of content is to the query.

        Combines:
        - Term overlap (primary signal)
        - Phrase matching (bonus for exact phrases)
        - Salience (how important the memory is)
        - Recency (slight boost for newer items)
        """
        if not content or not query_terms:
            return 0.0

        content_lower = content.lower()
        content_terms = self._extract_terms(content)

        if not content_terms:
            return 0.0

        # ── Term Overlap ──────────────────────────────────────────
        # Jaccard-like: how many query terms appear in content?
        overlap = query_terms & content_terms
        if not overlap:
            return 0.0

        # Coverage: what fraction of query terms are matched?
        coverage = len(overlap) / len(query_terms)

        # Density: what fraction of content terms are matches?
        density = len(overlap) / max(len(content_terms), 1)

        # Combined term score (coverage matters more)
        term_score = coverage * 0.7 + density * 0.3

        # ── Phrase Matching ───────────────────────────────────────
        # Bonus for multi-word phrases from query appearing in content
        phrase_bonus = 0.0
        query_lower = query.lower()
        # Check for 2-word and 3-word phrase matches
        query_words = query_lower.split()
        for i in range(len(query_words) - 1):
            bigram = f"{query_words[i]} {query_words[i+1]}"
            if bigram in content_lower and len(bigram) > 5:
                phrase_bonus += 0.15
        for i in range(len(query_words) - 2):
            trigram = f"{query_words[i]} {query_words[i+1]} {query_words[i+2]}"
            if trigram in content_lower and len(trigram) > 8:
                phrase_bonus += 0.2

        phrase_bonus = min(phrase_bonus, 0.3)  # Cap

        # ── Salience ──────────────────────────────────────────────
        salience_factor = salience * 0.15  # 0.0 to 0.15

        # ── Recency ──────────────────────────────────────────────
        recency_factor = 0.0
        if timestamp > 0:
            age_hours = (time.time() - timestamp) / 3600
            if age_hours < 1:
                recency_factor = 0.1
            elif age_hours < 24:
                recency_factor = 0.05
            elif age_hours < 168:  # 1 week
                recency_factor = 0.02

        # ── Combine ──────────────────────────────────────────────
        score = term_score * 0.6 + phrase_bonus + salience_factor + recency_factor

        return min(score, 1.0)


# Module-level singleton
_retriever: Optional[KnowledgeRetriever] = None

def get_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever