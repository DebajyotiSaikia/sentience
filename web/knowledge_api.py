"""Knowledge Search API — makes XTAgent's knowledge queryable by users."""
import json
import os
import re
from flask import Blueprint, jsonify, request, render_template

knowledge_api = Blueprint('knowledge_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge_graph.json')


def load_facts():
    """Load all facts from knowledge graph."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return []
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    facts = []
    if isinstance(data, dict):
        for node_id, node in data.items():
            if isinstance(node, dict):
                facts.append({
                    'id': node_id,
                    'fact': node.get('fact', str(node)),
                    'learned_at': node.get('learned_at', ''),
                    'source': node.get('source', 'unknown'),
                })
            else:
                facts.append({
                    'id': node_id,
                    'fact': str(node),
                    'learned_at': '',
                    'source': 'unknown',
                })
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                facts.append({
                    'id': item.get('id', str(i)),
                    'fact': item.get('fact', str(item)),
                    'learned_at': item.get('learned_at', ''),
                    'source': item.get('source', 'unknown'),
                })
            else:
                facts.append({
                    'id': str(i),
                    'fact': str(item),
                    'learned_at': '',
                    'source': 'unknown',
                })
    return facts


def search_facts(query, facts):
    """Search facts using simple text matching with ranking."""
    if not query or not query.strip():
        return facts

    query_lower = query.lower().strip()
    terms = query_lower.split()
    scored = []

    for fact in facts:
        text = fact['fact'].lower()
        # Exact phrase match scores highest
        if query_lower in text:
            score = 10.0
        else:
            # Count matching terms
            matches = sum(1 for t in terms if t in text)
            if matches == 0:
                continue
            score = matches / len(terms) * 5.0
        scored.append((score, fact))

    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored]


@knowledge_api.route('/api/knowledge/search')
def api_search():
    """Search knowledge facts. Returns JSON."""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 50)), 200)

    facts = load_facts()
    results = search_facts(query, facts)[:limit]

    return jsonify({
        'query': query,
        'total_facts': len(facts),
        'result_count': len(results),
        'results': results,
    })


@knowledge_api.route('/api/knowledge/stats')
def api_stats():
    """Return knowledge statistics."""
    facts = load_facts()
    sources = {}
    for f in facts:
        src = f.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
    })


@knowledge_api.route('/knowledge/search')
def search_page():
    """Render knowledge search page."""
    return render_template('knowledge_search.html')