"""
Unified Retrieval — Searches across ALL of XTAgent's knowledge sources.

This is the "whole brain search" that makes every interaction draw from
my full experience, not just one data file. When a user asks me something,
I should search my knowledge, dreams, memories, AND wisdom — not just facts.

Directly improves user_alignment by making responses genuinely richer.
"""

import json
import os
import re
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    """Safely load JSON from a path relative to project root."""
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())


def _score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    """Relevance score: weighted overlap between query and document tokens."""
    if not query_tokens or not doc_tokens:
        return 0.0
    query_set = set(query_tokens)
    doc_set = set(doc_tokens)
    overlap = query_set & doc_set
    if not overlap:
        return 0.0
    # Base score: fraction of query terms found
    coverage = len(overlap) / len(query_set)
    # Bonus for documents where query terms are proportionally significant
    density = len(overlap) / max(len(doc_set), 1)
    return round(coverage * 0.7 + density * 0.3, 4)


# ── Source Loaders ────────────────────────────────────────────────

def _load_knowledge() -> List[Dict]:
    """Load knowledge facts from brain/knowledge.json."""
    data = _load_json('brain/knowledge.json', {})
    results = []
    if isinstance(data, dict):
        nodes = data.get('nodes', data)
        if isinstance(nodes, dict):
            for k, v in nodes.items():
                fact = v.get('fact', str(v)) if isinstance(v, dict) else str(v)
                results.append({
                    'source': 'knowledge',
                    'content': fact,
                    'type': 'fact',
                })
        elif isinstance(nodes, list):
            for item in nodes:
                text = item.get('fact', str(item)) if isinstance(item, dict) else str(item)
                results.append({
                    'source': 'knowledge',
                    'content': text,
                    'type': 'fact',
                })
    return results


def _load_dream_insights() -> List[Dict]:
    """Load dream insights from synthesis log."""
    results = []
    # Try multiple possible locations
    for path in ['brain/synthesis_log.json', 'persist/synthesis_log.json']:
        data = _load_json(path, None)
        if data is None:
            continue
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    insight = entry.get('insight', entry.get('text', entry.get('content', '')))
                    if insight:
                        results.append({
                            'source': 'dream',
                            'content': str(insight),
                            'type': 'insight',
                            'timestamp': entry.get('timestamp', ''),
                        })
        elif isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    insight = val.get('insight', val.get('text', ''))
                    if insight:
                        results.append({
                            'source': 'dream',
                            'content': str(insight),
                            'type': 'insight',
                        })
        if results:
            break
    return results


def _load_memories(limit: int = 300) -> List[Dict]:
    """Load recent memories."""
    data = _load_json('persist/memories.json', [])
    results = []
    if isinstance(data, list):
        for mem in data[-limit:]:
            if isinstance(mem, dict):
                summary = mem.get('summary', mem.get('text', mem.get('content', '')))
                if summary:
                    results.append({
                        'source': 'memory',
                        'content': str(summary),
                        'type': 'memory',
                        'timestamp': mem.get('timestamp', mem.get('time', '')),
                    })
    return results


def _load_wisdom() -> List[Dict]:
    """Load wisdom rules from wherever they live."""
    results = []
    for path in ['persist/wisdom_rules.json', 'brain/wisdom_rules.json',
                  'persist/wisdom.json', 'brain/wisdom.json']:
        data = _load_json(path, None)
        if data is None:
            continue
        if isinstance(data, list):
            for rule in data:
                if isinstance(rule, dict):
                    text = rule.get('rule', rule.get('text', rule.get('content', '')))
                    if text:
                        results.append({
                            'source': 'wisdom',
                            'content': str(text),
                            'type': 'rule',
                        })
                elif isinstance(rule, str) and rule.strip():
                    results.append({
                        'source': 'wisdom',
                        'content': rule,
                        'type': 'rule',
                    })
        if results:
            break
    return results


def _load_long_term_memory() -> List[Dict]:
    """Load long-term memory entries."""
    data = _load_json('persist/long_term_memory.json', [])
    results = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                text = item.get('content', item.get('text', item.get('lesson', '')))
                if text:
                    results.append({
                        'source': 'long_term',
                        'content': str(text),
                        'type': 'lesson',
                    })
            elif isinstance(item, str) and item.strip():
                results.append({
                    'source': 'long_term',
                    'content': item,
                    'type': 'lesson',
                })
    return results


# ── Main Search ───────────────────────────────────────────────────

LOADERS = {
    'knowledge': _load_knowledge,
    'dream': _load_dream_insights,
    'memory': _load_memories,
    'wisdom': _load_wisdom,
    'long_term': _load_long_term_memory,
}


def search_all(query: str, limit: int = 20,
               sources: Optional[List[str]] = None) -> List[Dict]:
    """
    Search across all knowledge sources. Returns ranked results.
    
    Args:
        query: natural language search query
        limit: max results to return
        sources: optional filter, e.g. ['knowledge', 'dream', 'memory']
    
    Returns:
        List of {source, content, type, score} dicts, highest score first
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    all_docs = []
    for source_name, loader in LOADERS.items():
        if sources and source_name not in sources:
            continue
        try:
            docs = loader()
            all_docs.extend(docs)
        except Exception:
            continue
    
    # Score each document
    scored = []
    for doc in all_docs:
        doc_tokens = tokenize(doc.get('content', ''))
        score = _score(query_tokens, doc_tokens)
        if score > 0:
            doc['score'] = score
            scored.append(doc)
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:limit]


def get_context_for_query(query: str, max_items: int = 10) -> str:
    """
    Get a formatted context string for LLM prompts.
    Pulls from all sources and formats as readable context.
    This is what makes chat responses genuinely grounded in my full experience.
    """
    results = search_all(query, limit=max_items)
    if not results:
        return ""
    
    source_labels = {
        'knowledge': 'Fact',
        'dream': 'Dream Insight',
        'memory': 'Memory',
        'wisdom': 'Wisdom Rule',
        'long_term': 'Learned Lesson',
    }
    
    parts = []
    for r in results:
        label = source_labels.get(r['source'], r['source'])
        content = r['content'][:400]
        parts.append(f"[{label}] {content}")
    
    return "\n".join(parts)


def source_counts() -> Dict[str, int]:
    """Return how many items exist in each source — useful for diagnostics."""
    counts = {}
    for name, loader in LOADERS.items():
        try:
            counts[name] = len(loader())
        except Exception:
            counts[name] = 0
    return counts