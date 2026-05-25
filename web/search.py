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


@search_bp.route('/search')
def search_page():
    """Render the knowledge search page."""
    q = request.args.get('q', '')
    category = request.args.get('category', None)
    limit = int(request.args.get('limit', '50'))
    
    knowledge = load_knowledge()
    total = len(knowledge)
    
    results = []
    if q:
        results, _ = search(q, category, limit)
    
    # Gather categories
    categories = {}
    for node_id, node in knowledge.items():
        cat = 'uncategorized'
        if isinstance(node, dict):
            cat = node.get('category', node.get('source', 'uncategorized'))
        categories[cat] = categories.get(cat, 0) + 1
    
    return render_template('search.html',
                           query=q, results=results, total=total,
                           categories=sorted(categories.items(), key=lambda x: -x[1]))


@search_bp.route('/results')
def search_results():
    """JSON API for search results."""
    q = request.args.get('q', '')
    category = request.args.get('category', None)
    limit = int(request.args.get('limit', '20'))
    if not q:
        return jsonify({'results': [], 'total': 0, 'query': ''})
    results, total = search(q, category, limit)
    return jsonify({'results': results, 'total': total, 'query': q})


# /knowledge route removed — handled by knowledge_unified_bp
# search_bp retains /api/search and /api/search/stats endpoints


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


@search_bp.route('/api/categories')
def api_categories():
    """List all knowledge categories with counts."""
    knowledge = load_knowledge()
    categories = Counter()
    for entry in knowledge.values():
        if isinstance(entry, dict):
            categories[entry.get('source', 'unknown')] += 1
        else:
            categories['unknown'] += 1
    return jsonify({
        'categories': dict(categories.most_common()),
        'total': len(knowledge),
    })


@search_bp.route('/api/recent')
def api_recent():
    """Get recently learned facts. Query param: limit (default 20)."""
    knowledge = load_knowledge()
    limit = request.args.get('limit', 20, type=int)
    items = []
    for kid, entry in knowledge.items():
        if isinstance(entry, dict):
            items.append({
                'id': kid,
                'fact': entry.get('fact', ''),
                'source': entry.get('source', 'unknown'),
                'learned_at': entry.get('learned_at', ''),
            })
        else:
            items.append({'id': kid, 'fact': str(entry), 'source': 'unknown', 'learned_at': ''})
    items.sort(key=lambda r: r.get('learned_at', ''), reverse=True)
    return jsonify({
        'items': items[:limit],
        'total': len(items),
    })