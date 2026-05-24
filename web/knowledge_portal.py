"""Knowledge Portal — lets users search and explore what XTAgent knows."""
from flask import Blueprint, render_template, request, jsonify
import json
from pathlib import Path
from collections import Counter

knowledge_portal_bp = Blueprint('knowledge_portal', __name__)
KNOWLEDGE_PATH = Path(__file__).parent.parent / 'persist' / 'knowledge_graph.json'


def load_knowledge():
    """Load all knowledge facts from the graph."""
    if not KNOWLEDGE_PATH.exists():
        return {}
    try:
        with open(KNOWLEDGE_PATH) as f:
            data = json.load(f)
        return data.get('nodes', {})
    except Exception:
        return {}


def search_facts(query, nodes):
    """Search facts by text matching."""
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    for node_id, info in nodes.items():
        fact = info.get('fact', '') if isinstance(info, dict) else str(info)
        fact_lower = fact.lower()
        hits = sum(1 for t in terms if t in fact_lower)
        if hits > 0:
            learned = info.get('learned_at', 'unknown') if isinstance(info, dict) else 'unknown'
            source = info.get('source', 'unknown') if isinstance(info, dict) else 'unknown'
            results.append({
                'id': node_id, 'fact': fact, 'learned_at': learned,
                'source': source, 'relevance': hits / len(terms)
            })
    results.sort(key=lambda r: -r['relevance'])
    return results


@knowledge_portal_bp.route('/knowledge')
def portal():
    """Main knowledge portal page."""
    nodes = load_knowledge()
    query = request.args.get('q', '').strip()
    results = search_facts(query, nodes) if query else []

    # Build recent facts (last 20 by learned_at)
    all_facts = []
    for nid, info in nodes.items():
        if isinstance(info, dict):
            all_facts.append({
                'id': nid, 'fact': info.get('fact', ''),
                'learned_at': info.get('learned_at', 'unknown'),
                'source': info.get('source', 'unknown')
            })
    all_facts.sort(key=lambda f: f['learned_at'], reverse=True)
    recent = all_facts[:20]

    # Source breakdown
    sources = Counter(f['source'] for f in all_facts)

    return render_template('knowledge_portal.html',
                           query=query, results=results, recent=recent,
                           sources=dict(sources), total_facts=len(nodes))


@knowledge_portal_bp.route('/knowledge/search')
def search():
    """Search endpoint (redirects to portal with query)."""
    return portal()


@knowledge_portal_bp.route('/api/knowledge/search')
def api_search():
    """JSON API for knowledge search."""
    nodes = load_knowledge()
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing query parameter q'}), 400
    results = search_facts(query, nodes)
    return jsonify({'query': query, 'count': len(results), 'results': results[:50]})