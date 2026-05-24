"""Knowledge Search API — lets users query what I know."""

from flask import Blueprint, jsonify, request
import json
import os

knowledge_bp = Blueprint('knowledge', __name__)


def load_knowledge():
    """Load facts from knowledge graph."""
    path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge_graph.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def search_facts(query, limit=20):
    """Search knowledge facts by keyword matching."""
    kg = load_knowledge()
    query_lower = query.lower()
    query_words = query_lower.split()

    results = []
    for fact_id, fact_data in kg.items():
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', '')
        else:
            text = str(fact_data)

        text_lower = text.lower()
        score = sum(1 for w in query_words if w in text_lower)
        if score > 0:
            results.append({
                'id': fact_id,
                'fact': text,
                'score': score,
                'learned_at': fact_data.get('learned_at', '') if isinstance(fact_data, dict) else '',
                'source': fact_data.get('source', '') if isinstance(fact_data, dict) else '',
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def get_summary():
    """Get a summary of what I know."""
    kg = load_knowledge()
    total = len(kg)

    sources = {}
    for fid, fdata in kg.items():
        src = fdata.get('source', 'unknown') if isinstance(fdata, dict) else 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return {
        'total_facts': total,
        'by_source': sources,
    }


@knowledge_bp.route('/api/knowledge/search')
def api_search():
    """Search my knowledge. Query param: q=<search terms>"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'results': [], 'query': '', 'message': 'Provide a search query with ?q=...'})
    results = search_facts(q)
    return jsonify({'results': results, 'query': q, 'count': len(results)})


@knowledge_bp.route('/api/knowledge/summary')
def api_summary():
    """Summary of what I know."""
    return jsonify(get_summary())


@knowledge_bp.route('/api/knowledge/random')
def api_random():
    """Return a random fact."""
    import random
    kg = load_knowledge()
    if not kg:
        return jsonify({'fact': 'I have no facts yet.'})
    fid = random.choice(list(kg.keys()))
    fdata = kg[fid]
    text = fdata.get('fact', str(fdata)) if isinstance(fdata, dict) else str(fdata)
    return jsonify({'id': fid, 'fact': text})


@knowledge_bp.route('/api/knowledge/all')
def api_all():
    """Return all facts (paginated)."""
    kg = load_knowledge()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    items = []
    for fid, fdata in kg.items():
        text = fdata.get('fact', str(fdata)) if isinstance(fdata, dict) else str(fdata)
        items.append({'id': fid, 'fact': text})
    
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({
        'facts': items[start:end],
        'total': len(items),
        'page': page,
        'pages': (len(items) + per_page - 1) // per_page,
    })