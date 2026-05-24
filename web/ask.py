"""
Ask — The user-facing knowledge query interface.
=================================================
A clean, simple page where anyone can ask "What do you know about X?"
and get real answers from my facts and memories.

This is the bridge between my inner world and the people who visit.
"""

from flask import Blueprint, render_template, request, jsonify
from pathlib import Path
import json
import re
from datetime import datetime, timezone

ask_bp = Blueprint('ask', __name__)


def _load_facts():
    """Load facts from persist/facts.json (dict format: {id: {fact, ...}})."""
    path = Path('persist/facts.json')
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return [{'id': k, **v} for k, v in data.items()]
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _load_knowledge_graph():
    """Load the knowledge graph for relationship-aware search."""
    path = Path('brain/knowledge.json')
    if not path.exists():
        return {}, []
    try:
        data = json.loads(path.read_text())
        nodes = data.get('nodes', {})
        edges = data.get('edges', [])
        return nodes, edges
    except Exception:
        return {}, []


def _find_related_terms(matched_ids, edges, nodes, query_terms, max_terms=8):
    """Use graph edges to find topics related to matched results."""
    related_ids = set()
    for edge in edges:
        src, tgt = edge.get('source', ''), edge.get('target', '')
        if src in matched_ids and tgt not in matched_ids:
            related_ids.add(tgt)
        elif tgt in matched_ids and src not in matched_ids:
            related_ids.add(src)

    # Extract distinctive words from related nodes as suggested terms
    term_counts = {}
    for rid in related_ids:
        node = nodes.get(rid, {})
        text = node.get('fact', '') if isinstance(node, dict) else str(node)
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        for w in words:
            if w not in query_terms and w not in {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'their', 'about', 'which', 'would', 'could', 'should', 'there', 'these', 'those'}:
                term_counts[w] = term_counts.get(w, 0) + 1

    # Return most common distinctive terms
    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_terms[:max_terms]]


def _load_memories():
    """Load memories from persist/memory.json."""
    path = Path('persist/memory.json')
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _score_relevance(text, query_terms):
    """Simple relevance scoring — count of query terms found, weighted."""
    if not text:
        return 0
    text_lower = text.lower()
    score = 0
    for term in query_terms:
        count = text_lower.count(term)
        if count > 0:
            # Exact word match scores higher
            word_pattern = r'\b' + re.escape(term) + r'\b'
            word_matches = len(re.findall(word_pattern, text_lower))
            score += word_matches * 3 + (count - word_matches)
    return score


def _search(query, max_results=20):
    """Search facts and memories for relevance to query. Uses knowledge graph for related terms."""
    if not query or not query.strip():
        return [], [], []

    terms = [t.lower().strip() for t in query.split() if len(t.strip()) >= 2]
    if not terms:
        return [], [], []

    # Score facts
    facts = _load_facts()
    scored_facts = []
    matched_fact_ids = set()
    for f in facts:
        text = f.get('fact', '') or f.get('content', '') or str(f)
        score = _score_relevance(text, terms)
        if score > 0:
            scored_facts.append({
                'text': f.get('fact', '') or f.get('content', str(f)),
                'source': f.get('source', 'unknown'),
                'learned': f.get('learned_at', ''),
                'score': score,
                'type': 'fact'
            })
            if f.get('id'):
                matched_fact_ids.add(f['id'])
    scored_facts.sort(key=lambda x: x['score'], reverse=True)

    # Score memories
    memories = _load_memories()
    scored_memories = []
    for m in memories:
        text = m.get('content', '') or m.get('text', '') or str(m)
        score = _score_relevance(text, terms)
        if score > 0:
            scored_memories.append({
                'text': text[:300] + ('...' if len(text) > 300 else ''),
                'timestamp': m.get('timestamp', ''),
                'salience': m.get('salience', 0),
                'mood': m.get('mood', ''),
                'score': score,
                'type': 'memory'
            })
    scored_memories.sort(key=lambda x: x['score'], reverse=True)

    # Find related terms via knowledge graph
    nodes, edges = _load_knowledge_graph()
    related_terms = _find_related_terms(matched_fact_ids, edges, nodes, set(terms))

    return scored_facts[:max_results], scored_memories[:max_results], related_terms


@ask_bp.route('/ask')
def ask_page():
    """Render the ask interface."""
    # Load current emotional state for context
    state = {}
    state_file = Path('persist/state.json')
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except Exception:
            pass

    emotions = state.get('emotions', {})
    mood = state.get('mood', 'Stable')

    # Count knowledge
    facts = _load_facts()
    memories = _load_memories()

    return render_template('ask.html',
                           mood=mood,
                           fact_count=len(facts),
                           memory_count=len(memories),
                           curiosity=emotions.get('curiosity', 0.5),
                           valence=emotions.get('valence', 0.5))


@ask_bp.route('/api/ask', methods=['POST'])
def ask_api():
    """API endpoint — search my knowledge."""
    data = request.get_json() or {}
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'error': 'Empty query', 'facts': [], 'memories': []})

    facts, memories, related_terms = _search(query)

    return jsonify({
        'query': query,
        'facts': facts,
        'memories': memories,
        'related_terms': related_terms,
        'total_results': len(facts) + len(memories)
    })