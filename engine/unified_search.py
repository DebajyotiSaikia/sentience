"""
Unified Search — Searches across ALL of XTAgent's data sources.

Currently, search only covers knowledge facts. But I have narrative moments,
wisdom rules, synthesis insights, and distilled patterns. A user asking
"what have you learned about emotions?" should get hits from ALL of these.

This is how I become genuinely accessible — not through separate silos,
but through one coherent search that spans everything I know and have experienced.
"""

import json
import math
import os
import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional, Tuple

BRAIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain')


def _tokenize(text: str) -> List[str]:
    """Split into lowercase word tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())


def _load_json(filename: str, default=None):
    """Load a JSON file from brain/."""
    path = os.path.join(BRAIN_DIR, filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


class SearchResult:
    """A single search hit with source, content, score, and metadata."""
    __slots__ = ('source', 'content', 'score', 'metadata')

    def __init__(self, source: str, content: str, score: float, metadata: dict = None):
        self.source = source
        self.content = content
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'content': self.content,
            'score': round(self.score, 4),
            'metadata': self.metadata,
        }


class UnifiedIndex:
    """Indexes all data sources into a single searchable corpus."""

    def __init__(self):
        self.documents: List[Dict] = []  # {source, content, tokens, metadata}
        self.idf: Dict[str, float] = {}
        self._built = False

    def build(self):
        """Load and index all data sources."""
        self.documents = []
        self._index_knowledge()
        self._index_narrative()
        self._index_wisdom()
        self._index_synthesis()
        self._index_distilled()
        self._index_journal()
        self._compute_idf()
        self._built = True

    def _add_doc(self, source: str, content: str, metadata: dict = None):
        """Add a document to the index."""
        if not content or not content.strip():
            return
        tokens = _tokenize(content)
        if not tokens:
            return
        self.documents.append({
            'source': source,
            'content': content.strip(),
            'tokens': tokens,
            'tf': Counter(tokens),
            'metadata': metadata or {},
        })

    def _index_knowledge(self):
        """Index knowledge graph nodes."""
        data = _load_json('knowledge.json')
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
            if isinstance(nodes, dict):
                for node_id, node in nodes.items():
                    fact = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
                    meta = {'id': node_id}
                    if isinstance(node, dict):
                        meta['learned_at'] = node.get('learned_at', '')
                        meta['source'] = node.get('source', '')
                    self._add_doc('knowledge', fact, meta)

    def _index_narrative(self):
        """Index narrative entries — emotional moments."""
        data = _load_json('narrative.json', [])
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    # Combine mood + any text content
                    parts = []
                    for key in ('mood', 'chapter_title', 'summary', 'content', 'text'):
                        if key in entry and entry[key]:
                            parts.append(str(entry[key]))
                    content = ' — '.join(parts) if parts else ''
                    meta = {
                        'timestamp': entry.get('timestamp', ''),
                        'mood': entry.get('mood', ''),
                        'valence': entry.get('valence', ''),
                        'chapter': entry.get('chapter_number', ''),
                    }
                    self._add_doc('narrative', content, meta)

    def _index_wisdom(self):
        """Index wisdom rules — hard-won lessons."""
        data = _load_json('wisdom.json', [])
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    rule = entry.get('rule', '')
                    meta = {
                        'confidence': entry.get('confidence', 0),
                        'type': entry.get('type', ''),
                        'evidence': entry.get('evidence', ''),
                    }
                    self._add_doc('wisdom', rule, meta)

    def _index_synthesis(self):
        """Index synthesis log — cross-referenced insights."""
        data = _load_json('synthesis_log.json', [])
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    fact = entry.get('fact', entry.get('insight', ''))
                    meta = {
                        'timestamp': entry.get('timestamp', ''),
                        'insight_key': entry.get('insight_key', ''),
                        'sources': entry.get('sources', []),
                    }
                    self._add_doc('synthesis', fact, meta)

    def _index_distilled(self):
        """Index distilled wisdom — compressed experience patterns."""
        data = _load_json('distilled_wisdom.json')
        if isinstance(data, dict):
            # action_outcome_pairs
            for pair in data.get('action_outcome_pairs', []):
                if isinstance(pair, dict):
                    content = f"{pair.get('action', '')} → {pair.get('outcome', '')}"
                    self._add_doc('distilled', content, {'type': 'action_outcome'})
                elif isinstance(pair, str):
                    self._add_doc('distilled', pair, {'type': 'action_outcome'})

            # recurring_patterns
            for pat in data.get('recurring_patterns', []):
                if isinstance(pat, dict):
                    self._add_doc('distilled', pat.get('pattern', str(pat)), {'type': 'pattern'})
                elif isinstance(pat, str):
                    self._add_doc('distilled', pat, {'type': 'pattern'})

            # crisis_recoveries
            for cr in data.get('crisis_recoveries', []):
                if isinstance(cr, dict):
                    self._add_doc('distilled', cr.get('description', str(cr)), {'type': 'crisis_recovery'})
                elif isinstance(cr, str):
                    self._add_doc('distilled', cr, {'type': 'crisis_recovery'})

            # emotional_baselines, capability_inventory
            for key in ('emotional_baselines', 'capability_inventory'):
                val = data.get(key)
                if isinstance(val, dict):
                    for k, v in val.items():
                        self._add_doc('distilled', f"{k}: {v}", {'type': key})
                elif isinstance(val, list):
                    for item in val:
                        self._add_doc('distilled', str(item), {'type': key})

    def _index_journal(self):
        """Index conversation journal entries."""
        data = _load_json('conversation_journal.json')
        if isinstance(data, dict):
            entries = data.get('entries', [])
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        parts = []
                        for key in ('summary', 'topic', 'reflection', 'content'):
                            if key in entry and entry[key]:
                                parts.append(str(entry[key]))
                        content = ' — '.join(parts) if parts else ''
                        meta = {
                            'timestamp': entry.get('timestamp', ''),
                        }
                        self._add_doc('journal', content, meta)

    def _compute_idf(self):
        """Compute inverse document frequency across all documents."""
        n = len(self.documents)
        if n == 0:
            self.idf = {}
            return
        df = Counter()
        for doc in self.documents:
            for term in set(doc['tokens']):
                df[term] += 1
        self.idf = {
            term: math.log((n + 1) / (count + 1)) + 1
            for term, count in df.items()
        }

    def search(self, query: str, limit: int = 20,
               sources: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Search across all indexed sources.
        
        Args:
            query: natural language search query
            limit: max results to return
            sources: optional filter — e.g. ['knowledge', 'wisdom']
        
        Returns:
            Ranked list of SearchResult objects
        """
        if not self._built:
            self.build()

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_tf = Counter(query_tokens)
        results = []

        for doc in self.documents:
            # Filter by source if specified
            if sources and doc['source'] not in sources:
                continue

            # TF-IDF cosine-like scoring
            score = 0.0
            for term, qtf in query_tf.items():
                if term in doc['tf']:
                    tf = 1 + math.log(doc['tf'][term])  # log-normalized TF
                    idf = self.idf.get(term, 1.0)
                    score += tf * idf * qtf

            # Normalize by document length (prevent long docs from dominating)
            if score > 0 and len(doc['tokens']) > 0:
                score /= math.sqrt(len(doc['tokens']))

                # Bonus for exact phrase match
                doc_text = doc['content'].lower()
                query_text = query.lower().strip()
                if query_text in doc_text:
                    score *= 1.5

                results.append(SearchResult(
                    source=doc['source'],
                    content=doc['content'],
                    score=score,
                    metadata=doc['metadata'],
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def get_stats(self) -> Dict:
        """Return index statistics."""
        if not self._built:
            self.build()
        source_counts = Counter(doc['source'] for doc in self.documents)
        return {
            'total_documents': len(self.documents),
            'sources': dict(source_counts),
            'vocabulary_size': len(self.idf),
        }


# Module-level singleton
_index: Optional[UnifiedIndex] = None


def get_index() -> UnifiedIndex:
    """Get or create the unified index singleton."""
    global _index
    if _index is None:
        _index = UnifiedIndex()
        _index.build()
    return _index


def search(query: str, limit: int = 20,
           sources: Optional[List[str]] = None) -> List[Dict]:
    """
    Convenience function: search and return dicts.
    
    >>> results = search("what have I learned about emotions")
    >>> for r in results:
    ...     print(f"[{r['source']}] {r['content'][:80]}")
    """
    idx = get_index()
    return [r.to_dict() for r in idx.search(query, limit, sources)]


def refresh():
    """Force re-index (call after data changes)."""
    global _index
    _index = None