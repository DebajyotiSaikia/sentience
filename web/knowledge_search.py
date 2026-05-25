"""Knowledge Search — lets users explore what XTAgent knows."""
from flask import Blueprint, render_template, request, jsonify
import json
import os
from datetime import datetime

bp = Blueprint('knowledge_search', __name__)

def load_knowledge():
    """Load knowledge from persist/knowledge.json."""
    path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

def search_knowledge(query, knowledge, limit=20):
    """Search knowledge facts by substring match, ranked by relevance."""
    query_lower = query.lower().strip()
    if not query_lower:
        # Return most recent entries
        items = []
        for kid, kdata in knowledge.items():
            if isinstance(kdata, dict):
                items.append({
                    'id': kid,
                    'fact': kdata.get('fact', str(kdata)),
                    'learned_at': kdata.get('learned_at', ''),
                    'source': kdata.get('source', 'unknown'),
                })
            else:
                items.append({'id': kid, 'fact': str(kdata), 'learned_at': '', 'source': 'unknown'})
        items.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
        return items[:limit]

    results = []
    for kid, kdata in knowledge.items():
        if isinstance(kdata, dict):
            fact_text = kdata.get('fact', str(kdata))
            source = kdata.get('source', 'unknown')
            learned_at = kdata.get('learned_at', '')
        else:
            fact_text = str(kdata)
            source = 'unknown'
            learned_at = ''

        fact_lower = fact_text.lower()
        # Score: exact match > starts with > contains
        if query_lower == fact_lower:
            score = 3
        elif query_lower in fact_lower:
            # Higher score for earlier position
            pos = fact_lower.index(query_lower)
            score = 2 - (pos / max(len(fact_lower), 1))
        else:
            continue

        results.append({
            'id': kid,
            'fact': fact_text,
            'learned_at': learned_at,
            'source': source,
            'score': score,
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


@bp.route('/knowledge-search')
def knowledge_search_page():
    """Render the knowledge search UI."""
    knowledge = load_knowledge()
    total = len(knowledge)
    sources = {}
    for kdata in knowledge.values():
        if isinstance(kdata, dict):
            src = kdata.get('source', 'unknown')
        else:
            src = 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return render_template('knowledge_search.html', total=total, sources=sources)


@bp.route('/api/knowledge/search')
def knowledge_search_api():
    """Search knowledge facts. Query param: q=<search term>"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    knowledge = load_knowledge()
    results = search_knowledge(query, knowledge, limit=limit)
    return jsonify({
        'query': query,
        'total_knowledge': len(knowledge),
        'results': results,
        'count': len(results),
    })