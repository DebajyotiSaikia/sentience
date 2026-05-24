"""Knowledge search functionality with Flask blueprint."""
import json
import os
import re
from collections import Counter
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def load_knowledge():
    """Load knowledge facts from persist/knowledge.json (graph format: {nodes, edges})."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {}
    with open(KNOWLEDGE_PATH, 'r') as f:
        data = json.load(f)
    # Knowledge file uses graph format {nodes: {id: {fact, ...}}, edges: [...]}
    if isinstance(data, dict) and 'nodes' in data:
        return data['nodes']
    return data


def search(query, category=None, limit=50):
    """Search knowledge base. Returns (results, total_count)."""
    knowledge = load_knowledge()
    results = []

    query_lower = query.lower().strip() if query else ''

    for kid, entry in knowledge.items():
        fact = entry.get('fact', '') if isinstance(entry, dict) else str(entry)
        source = entry.get('source', 'unknown') if isinstance(entry, dict) else 'unknown'
        learned = entry.get('learned_at', '') if isinstance(entry, dict) else ''

        # Category filter
        if category and source != category:
            continue

        # Query match (empty query = return all)
        if query_lower and query_lower not in fact.lower():
            continue

        results.append({
            'id': kid,
            'fact': fact,
            'source': source,
            'learned_at': learned,
        })

    # Sort by recency
    results.sort(key=lambda r: r.get('learned_at', ''), reverse=True)
    return results[:limit], len(knowledge)


def get_search_stats():
    """Get statistics about the knowledge base."""
    knowledge = load_knowledge()
    sources = Counter()
    categories = Counter()

    for entry in knowledge.values():
        if isinstance(entry, dict):
            sources[entry.get('source', 'unknown')] += 1
        else:
            sources['unknown'] += 1

    return {
        'total_facts': len(knowledge),
        'sources': dict(sources.most_common(10)),
    }


# --- Flask Blueprint ---
search_bp = Blueprint('search', __name__, template_folder='templates')


@search_bp.route('/knowledge')
def search_page():
    """Render the knowledge explorer page."""
    q = request.args.get('q', '')
    category = request.args.get('category', None)
    results = []
    if q:
        found, total = search(q, category=category)
        results = found
    stats = get_search_stats()
    return render_template('knowledge_search.html',
                           query=q, results=results,
                           facts=range(stats['total_facts']),
                           stats=stats)


@search_bp.route('/api/search')
def api_search():
    """Search knowledge base. Query params: q, category, limit."""
    q = request.args.get('q', '')
    category = request.args.get('category', None)
    limit = request.args.get('limit', 50, type=int)
    results, total = search(q, category=category, limit=limit)
    return jsonify({
        'query': q,
        'category': category,
        'total_knowledge': total,
        'result_count': len(results),
        'results': results,
    })


@search_bp.route('/api/search/stats')
def api_search_stats():
    """Get knowledge base statistics."""
    return jsonify(get_search_stats())