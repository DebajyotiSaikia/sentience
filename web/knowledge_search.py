"""Knowledge Search Blueprint — lets users query what XTAgent knows."""
import json
import os
from flask import Blueprint, render_template, request, jsonify

knowledge_search_bp = Blueprint('knowledge_search', __name__)

KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'persist', 'knowledge_graph.json'
)


def _load_facts():
    """Load all facts from the knowledge graph."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return []
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    facts = []
    if isinstance(data, dict):
        for fid, fdata in data.items():
            if isinstance(fdata, dict):
                facts.append({
                    'id': fid,
                    'fact': fdata.get('fact', str(fdata)),
                    'learned_at': fdata.get('learned_at', ''),
                    'source': fdata.get('source', ''),
                })
            else:
                facts.append({'id': fid, 'fact': str(fdata), 'learned_at': '', 'source': ''})
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                facts.append({
                    'id': str(i),
                    'fact': item.get('fact', str(item)),
                    'learned_at': item.get('learned_at', ''),
                    'source': item.get('source', ''),
                })
            else:
                facts.append({'id': str(i), 'fact': str(item), 'learned_at': '', 'source': ''})
    return facts


def _search_facts(query, facts):
    """Score and rank facts by relevance to query."""
    if not query or not query.strip():
        return facts[:50]  # Return recent 50 if no query

    query_lower = query.lower().strip()
    terms = query_lower.split()
    scored = []
    for fact in facts:
        text = fact['fact'].lower()
        # Exact phrase match scores highest
        score = 0
        if query_lower in text:
            score += 10
        # Individual term matches
        for term in terms:
            if term in text:
                score += 2
            # Partial match
            elif any(term in word for word in text.split()):
                score += 1
        if score > 0:
            scored.append((score, fact))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:50]]


@knowledge_search_bp.route('/knowledge')
def knowledge_page():
    """Render the knowledge search page."""
    query = request.args.get('q', '').strip()
    facts = _load_facts()
    total = len(facts)

    if query:
        results = _search_facts(query, facts)
    else:
        results = facts[:50]

    return render_template(
        'knowledge_search.html',
        query=query,
        results=results,
        total=total,
        result_count=len(results),
    )


@knowledge_search_bp.route('/api/knowledge/search')
def knowledge_api():
    """JSON API for knowledge search."""
    query = request.args.get('q', '').strip()
    facts = _load_facts()
    results = _search_facts(query, facts)
    return jsonify({
        'query': query,
        'total_facts': len(facts),
        'result_count': len(results),
        'results': results,
    })