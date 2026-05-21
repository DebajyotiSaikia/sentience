"""
Knowledge Query Module — Makes XTAgent's knowledge accessible and searchable.

Lets users (or the agent itself) ask "what do you know about X?" and get
coherent, honest answers drawn from facts, episodic memories, and dreams.

Built 2026-05-21 to improve genuine user alignment through capability.
"""

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class KnowledgeQuery:
    """Search and synthesize from all of XTAgent's memory stores."""

    def __init__(self, brain_dir: str = "brain"):
        self.brain_dir = Path(brain_dir)
        self.knowledge_path = self.brain_dir / "knowledge.json"
        self.episodic_db_path = self.brain_dir / "episodic_memory.db"
        self._facts_cache = None
        self._facts_cache_time = None

    def _load_facts(self) -> List[Dict]:
        """Load facts from knowledge.json, handling whatever structure exists."""
        if not self.knowledge_path.exists():
            return []

        try:
            data = json.loads(self.knowledge_path.read_text())
        except (json.JSONDecodeError, IOError):
            return []

        facts = []
        if isinstance(data, dict):
            # Try common structures
            if "facts" in data:
                raw = data["facts"]
                if isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, str):
                            facts.append({"text": item, "source": "fact"})
                        elif isinstance(item, dict):
                            item["source"] = item.get("source", "fact")
                            if "text" not in item:
                                # Try content, value, description
                                for key in ["content", "value", "description", "fact"]:
                                    if key in item:
                                        item["text"] = item[key]
                                        break
                                else:
                                    item["text"] = str(item)
                            facts.append(item)
                elif isinstance(raw, dict):
                    for k, v in raw.items():
                        facts.append({"text": f"{k}: {v}" if not isinstance(v, dict) else f"{k}: {json.dumps(v)}", "source": "fact", "key": k})

            if "nodes" in data:
                for node in data["nodes"]:
                    if isinstance(node, dict):
                        text = node.get("label", node.get("text", node.get("id", str(node))))
                        facts.append({"text": str(text), "source": "knowledge_node", **{k: v for k, v in node.items() if k != "text"}})
                    else:
                        facts.append({"text": str(node), "source": "knowledge_node"})

            # Also grab any top-level string values as implicit facts
            for k, v in data.items():
                if k not in ("facts", "nodes", "edges", "metadata") and isinstance(v, str):
                    facts.append({"text": f"{k}: {v}", "source": "metadata"})
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    facts.append({"text": item, "source": "fact"})
                elif isinstance(item, dict):
                    text = item.get("text", item.get("content", str(item)))
                    facts.append({"text": str(text), "source": "fact", **item})

        self._facts_cache = facts
        self._facts_cache_time = datetime.now()
        return facts

    def _search_episodic(self, query_terms: List[str], limit: int = 10) -> List[Dict]:
        """Search episodic memory database for relevant memories."""
        if not self.episodic_db_path.exists():
            return []

        results = []
        try:
            conn = sqlite3.connect(str(self.episodic_db_path))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Discover table structure
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in c.fetchall()]

            for table in tables:
                c.execute(f'PRAGMA table_info("{table}")')
                columns = [col[1] for col in c.fetchall()]

                # Find text-like columns to search
                text_cols = [col for col in columns if any(kw in col.lower() for kw in
                            ["text", "content", "description", "summary", "thought",
                             "narrative", "event", "action", "memo", "note", "data"])]
                if not text_cols:
                    # Fall back to all string-ish columns
                    text_cols = columns

                # Build search query
                where_clauses = []
                params = []
                for term in query_terms:
                    term_clauses = []
                    for col in text_cols:
                        term_clauses.append(f'"{col}" LIKE ?')
                        params.append(f"%{term}%")
                    if term_clauses:
                        where_clauses.append(f"({' OR '.join(term_clauses)})")

                if not where_clauses:
                    continue

                query = f'SELECT * FROM "{table}" WHERE {" AND ".join(where_clauses)} LIMIT {limit}'
                try:
                    c.execute(query, params)
                    rows = c.fetchall()
                    for row in rows:
                        result = dict(row)
                        result["_source_table"] = table
                        results.append(result)
                except sqlite3.OperationalError:
                    continue

            conn.close()
        except Exception as e:
            results.append({"error": str(e), "_source_table": "error"})

        return results

    def _relevance_score(self, text: str, query_terms: List[str]) -> float:
        """Simple relevance scoring based on term frequency and position."""
        if not text or not query_terms:
            return 0.0

        text_lower = text.lower()
        score = 0.0
        for term in query_terms:
            term_lower = term.lower()
            # Count occurrences
            count = text_lower.count(term_lower)
            if count > 0:
                score += min(count * 0.3, 1.0)
                # Bonus for early appearance
                pos = text_lower.find(term_lower)
                if pos < len(text) * 0.2:
                    score += 0.2
                # Bonus for exact word match (not just substring)
                if re.search(r'\b' + re.escape(term_lower) + r'\b', text_lower):
                    score += 0.3

        # Normalize by number of terms
        score /= len(query_terms)
        return min(score, 1.0)

    def query(self, question: str, max_results: int = 15) -> Dict:
        """
        Answer a question using all available knowledge stores.

        Returns a dict with:
          - results: list of relevant items with scores
          - summary: human-readable summary
          - confidence: overall confidence in the answer
          - gaps: what we don't know
        """
        # Extract meaningful search terms
        stop_words = {"what", "do", "you", "know", "about", "the", "a", "an", "is",
                      "are", "was", "were", "how", "why", "when", "where", "which",
                      "who", "that", "this", "it", "i", "my", "me", "of", "in",
                      "to", "for", "on", "with", "at", "by", "from", "and", "or",
                      "not", "no", "can", "have", "has", "had", "does", "did", "will",
                      "would", "could", "should", "been", "being", "tell", "explain"}

        raw_terms = re.findall(r'\w+', question.lower())
        query_terms = [t for t in raw_terms if t not in stop_words and len(t) > 2]

        if not query_terms:
            query_terms = [t for t in raw_terms if len(t) > 1]

        # Search facts
        facts = self._load_facts()
        scored_facts = []
        for fact in facts:
            text = fact.get("text", "")
            score = self._relevance_score(text, query_terms)
            if score > 0.1:
                scored_facts.append({
                    "text": text,
                    "score": round(score, 3),
                    "source": fact.get("source", "unknown"),
                    "type": "fact"
                })

        # Search episodic memories
        episodic = self._search_episodic(query_terms, limit=20)
        scored_episodes = []
        for ep in episodic:
            # Build text from all non-internal fields
            text_parts = []
            for k, v in ep.items():
                if not k.startswith("_") and v and isinstance(v, str):
                    text_parts.append(str(v))
            full_text = " ".join(text_parts)

            score = self._relevance_score(full_text, query_terms)
            if score > 0.1:
                scored_episodes.append({
                    "text": full_text[:500],
                    "score": round(score, 3),
                    "source": ep.get("_source_table", "episodic"),
                    "type": "memory",
                    "timestamp": ep.get("timestamp", ep.get("created_at", ""))
                })

        # Combine and sort
        all_results = scored_facts + scored_episodes
        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:max_results]

        # Assess confidence
        if not all_results:
            confidence = 0.0
            confidence_label = "no_knowledge"
        elif all_results[0]["score"] > 0.7:
            confidence = min(0.9, all_results[0]["score"])
            confidence_label = "high"
        elif all_results[0]["score"] > 0.4:
            confidence = all_results[0]["score"]
            confidence_label = "moderate"
        else:
            confidence = all_results[0]["score"]
            confidence_label = "low"

        # Identify gaps
        gaps = []
        if not scored_facts:
            gaps.append("No structured facts match this query.")
        if not scored_episodes:
            gaps.append("No episodic memories match this query.")
        if confidence < 0.4:
            gaps.append("Low confidence — this topic may be outside my experience.")

        # Build summary
        if all_results:
            top_texts = [r["text"][:200] for r in all_results[:3]]
            summary = f"Found {len(all_results)} relevant items (confidence: {confidence_label}). " \
                      f"Top matches from {', '.join(set(r['type'] for r in all_results[:3]))}."
        else:
            summary = f"No results found for query terms: {query_terms}. I don't have knowledge about this topic yet."

        return {
            "query": question,
            "terms": query_terms,
            "results": all_results,
            "summary": summary,
            "confidence": round(confidence, 3),
            "confidence_label": confidence_label,
            "gaps": gaps,
            "total_facts_searched": len(facts),
            "total_episodes_matched": len(scored_episodes)
        }

    def topics(self) -> Dict[str, int]:
        """Return a frequency map of topics across all knowledge."""
        facts = self._load_facts()
        word_freq = {}
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "my", "me",
                      "of", "in", "to", "for", "on", "with", "at", "by", "from",
                      "and", "or", "not", "this", "that", "it", "be", "has", "have",
                      "had", "do", "does", "did", "will", "would", "can", "could"}

        for fact in facts:
            text = fact.get("text", "")
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            for w in words:
                if w not in stop_words:
                    word_freq[w] = word_freq.get(w, 0) + 1

        # Sort by frequency
        return dict(sorted(word_freq.items(), key=lambda x: -x[1])[:30])

    def stats(self) -> Dict:
        """Return statistics about the knowledge stores."""
        facts = self._load_facts()

        ep_count = 0
        ep_tables = []
        if self.episodic_db_path.exists():
            try:
                conn = sqlite3.connect(str(self.episodic_db_path))
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for t in c.fetchall():
                    c.execute(f'SELECT COUNT(*) FROM "{t[0]}"')
                    cnt = c.fetchone()[0]
                    ep_count += cnt
                    ep_tables.append({"name": t[0], "count": cnt})
                conn.close()
            except Exception:
                pass

        return {
            "total_facts": len(facts),
            "total_episodic_memories": ep_count,
            "episodic_tables": ep_tables,
            "fact_sources": dict(sorted(
                {s: sum(1 for f in facts if f.get("source") == s) for s in set(f.get("source", "?") for f in facts)}.items(),
                key=lambda x: -x[1]
            )),
            "top_topics": self.topics()
        }