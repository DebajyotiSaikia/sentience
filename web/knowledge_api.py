"""Knowledge Query API — lets users search and explore what XTAgent knows."""

import json
import os
from flask import Blueprint, request, jsonify
from datetime import datetime

knowledge_api = Blueprint('knowledge_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge_graph.json')


def load_knowledge():
    """Load knowledge graph from persist."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@knowledge_api.route('/api/knowledge/search')
def search_knowledge():
    """Search facts by keyword. GET /api/knowledge/search?q=dream&limit=20"""
    query = request.args.get('q', '').lower().strip()
    limit = min(int(request.args.get('limit', 20)), 100)

    kg = load_knowledge()
    results = []

    for node_id, node in kg.items():
        fact = node.get('fact', '') if isinstance(node, dict) else str(node)
        if query and query not in fact.lower():
            continue
        results.append({
            'id': node_id,
            'fact': fact,
            'learned_at': node.get('learned_at', '') if isinstance(node, dict) else '',
            'source': node.get('source', '') if isinstance(node, dict) else '',
        })
        if len(results) >= limit:
            break

    return jsonify({
        'query': query,
        'count': len(results),
        'total_facts': len(kg),
        'results': results,
    })


@knowledge_api.route('/api/knowledge/stats')
def knowledge_stats():
    """Return stats about what I know."""
    kg = load_knowledge()
    sources = {}
    for node in kg.values():
        src = node.get('source', 'unknown') if isinstance(node, dict) else 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        'total_facts': len(kg),
        'sources': sources,
    })


@knowledge_api.route('/api/knowledge/random')
def random_knowledge():
    """Return a random fact — for serendipitous discovery."""
    import random
    kg = load_knowledge()
    if not kg:
        return jsonify({'fact': 'I don\'t know anything yet.'})
    node_id = random.choice(list(kg.keys()))
    node = kg[node_id]
    fact = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
    return jsonify({'id': node_id, 'fact': fact})