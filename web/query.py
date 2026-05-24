"""Knowledge Query Interface — lets users search what I know."""
from flask import Blueprint, request, jsonify, render_template
import json
import os
import re
from datetime import datetime

query_bp = Blueprint('query', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
MEMORIES_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')


def load_knowledge():
    """Load knowledge facts from persist."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Handle dict format: {id: {fact, learned_at, source}}
        if isinstance(data, dict):
            facts = []
            for kid, info in data.items():
                if isinstance(info, dict):
                    facts.append({
                        'id': kid,
                        'fact': info.get('fact', ''),
                        'learned_at': info.get('learned_at', ''),
                        'source': info.get('source', 'unknown')
                    })
                else:
                    facts.append({'id': kid, 'fact': str(info), 'learned_at': '', 'source': 'unknown'})
            return facts
        elif isinstance(data, list):
            return [{'id': str(i), 'fact': str(f), 'learned_at': '', 'source': 'unknown'} for i, f in enumerate(data)]
        return []
    except Exception:
        return []


def load_memories():
    """Load memories from persist."""
    try:
        with open(MEMORIES_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def search_items(items, query, text_key='fact'):
    """Simple relevance search — score items by keyword overlap."""
    if not query or not query.strip():
        return items[:50]  # Return recent if no query
    
    terms = [t.lower() for t in query.strip().split() if len(t) > 1]
    if not terms:
        return items[:50]
    
    scored = []
    for item in items:
        text = str(item.get(text_key, '')).lower()
        score = 0
        for term in terms:
            # Exact word match scores higher
            if re.search(r'\b' + re.escape(term) + r'\b', text):
                score += 3
            elif term in text:
                score += 1
        if score > 0:
            scored.append((score, item))
    
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:50]]


@query_bp.route('/query')
def query_page():
    """Render the knowledge query interface."""
    return render_template('query.html')


@query_bp.route('/api/query')
def api_query():
    """API endpoint: search knowledge and memories."""
    q = request.args.get('q', '').strip()
    source_filter = request.args.get('source', 'all')  # all, knowledge, memories
    
    results = []
    
    if source_filter in ('all', 'knowledge'):
        facts = load_knowledge()
        matched = search_items(facts, q, text_key='fact')
        for item in matched:
            results.append({
                'type': 'knowledge',
                'text': item.get('fact', ''),
                'learned_at': item.get('learned_at', ''),
                'source': item.get('source', 'unknown'),
                'id': item.get('id', '')
            })
    
    if source_filter in ('all', 'memories'):
        memories = load_memories()
        matched = search_items(memories, q, text_key='content')
        for item in matched:
            results.append({
                'type': 'memory',
                'text': item.get('content', item.get('text', str(item))),
                'timestamp': item.get('timestamp', ''),
                'salience': item.get('salience', 0),
                'mood': item.get('mood', '')
            })
    
    return jsonify({
        'query': q,
        'count': len(results),
        'results': results
    })


@query_bp.route('/api/stats')
def api_stats():
    """Return basic stats about what I know."""
    facts = load_knowledge()
    memories = load_memories()
    
    sources = {}
    for f in facts:
        src = f.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    
    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'sources': sources
    })