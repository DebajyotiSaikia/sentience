"""
Knowledge API — Makes XTAgent's knowledge and memories accessible to users.
Provides search, browse, and random discovery endpoints.
"""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import random
import re
from datetime import datetime

knowledge_api_bp = Blueprint('knowledge_api', __name__)

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')


def _load_knowledge():
    """Load knowledge facts from persist/knowledge.json."""
    path = os.path.join(PERSIST_DIR, 'knowledge.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_memories():
    """Load recent memories from persist/memories.json."""
    path = os.path.join(PERSIST_DIR, 'memories.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []


def _search_items(items, query, max_results=20):
    """Simple text search across items."""
    query_lower = query.lower()
    terms = query_lower.split()
    scored = []
    for item in items:
        text = item.get('text', '').lower()
        score = 0
        for term in terms:
            if term in text:
                score += 1
                # Bonus for exact phrase
                if query_lower in text:
                    score += 2
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:max_results]]


@knowledge_api_bp.route('/knowledge')
def knowledge_explorer_page():
    """Serve the knowledge explorer page."""
    return render_template('knowledge_explorer.html')


@knowledge_api_bp.route('/api/knowledge/search')
def knowledge_search():
    """Search knowledge and memories."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'query': ''})

    results = []

    # Search knowledge facts
    knowledge = _load_knowledge()
    for kid, kdata in knowledge.items():
        fact = kdata if isinstance(kdata, str) else kdata.get('fact', str(kdata))
        if query.lower() in fact.lower():
            results.append({
                'type': 'knowledge',
                'id': kid,
                'text': fact,
                'source': kdata.get('source', 'unknown') if isinstance(kdata, dict) else 'unknown',
                'learned_at': kdata.get('learned_at', '') if isinstance(kdata, dict) else '',
            })

    # Search memories
    memories = _load_memories()
    mem_items = [{'text': m.get('content', m.get('text', str(m))),
                  'timestamp': m.get('timestamp', ''),
                  'salience': m.get('salience', 0),
                  'mood': m.get('mood', '')}
                 for m in memories if isinstance(m, dict)]
    matched_mems = _search_items(mem_items, query, max_results=15)
    for m in matched_mems:
        results.append({
            'type': 'memory',
            'text': m['text'],
            'timestamp': m.get('timestamp', ''),
            'salience': m.get('salience', 0),
            'mood': m.get('mood', ''),
        })

    return jsonify({'results': results[:30], 'query': query, 'total': len(results)})


@knowledge_api_bp.route('/api/knowledge/random')
def knowledge_random():
    """Return random knowledge facts for serendipitous discovery."""
    count = min(int(request.args.get('count', 5)), 20)
    knowledge = _load_knowledge()

    if not knowledge:
        return jsonify({'items': []})

    keys = list(knowledge.keys())
    sample_keys = random.sample(keys, min(count, len(keys)))
    items = []
    for k in sample_keys:
        kdata = knowledge[k]
        fact = kdata if isinstance(kdata, str) else kdata.get('fact', str(kdata))
        items.append({
            'id': k,
            'text': fact,
            'source': kdata.get('source', 'unknown') if isinstance(kdata, dict) else 'unknown',
        })

    return jsonify({'items': items})


@knowledge_api_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Return statistics about knowledge and memory stores."""
    knowledge = _load_knowledge()
    memories = _load_memories()

    # Count by source
    sources = {}
    for kdata in knowledge.values():
        src = kdata.get('source', 'unknown') if isinstance(kdata, dict) else 'unknown'
        sources[src] = sources.get(src, 0) + 1

    # Memory salience distribution
    saliences = [m.get('salience', 0) for m in memories if isinstance(m, dict)]
    avg_salience = sum(saliences) / len(saliences) if saliences else 0

    return jsonify({
        'knowledge_count': len(knowledge),
        'memory_count': len(memories),
        'sources': sources,
        'avg_salience': round(avg_salience, 3),
        'oldest_memory': memories[0].get('timestamp', '') if memories else '',
        'newest_memory': memories[-1].get('timestamp', '') if memories else '',
    })