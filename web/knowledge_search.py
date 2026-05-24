"""Knowledge Search - lets users explore what I know."""
import json
import os
from flask import Blueprint, render_template, request, jsonify

knowledge_search_bp = Blueprint('knowledge_search', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def load_knowledge():
    """Load knowledge facts from brain/knowledge.json."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Handle both dict-of-dicts and list formats
        if isinstance(data, dict):
            facts = []
            for kid, v in data.items():
                if isinstance(v, dict):
                    facts.append({
                        'id': kid,
                        'fact': v.get('fact', str(v)),
                        'learned_at': v.get('learned_at', ''),
                        'source': v.get('source', ''),
                    })
                else:
                    facts.append({'id': kid, 'fact': str(v), 'learned_at': '', 'source': ''})
            return facts
        elif isinstance(data, list):
            return [{'id': str(i), 'fact': str(item), 'learned_at': '', 'source': ''} for i, item in enumerate(data)]
        return []
    except Exception as e:
        return [{'id': 'error', 'fact': f'Failed to load knowledge: {e}', 'learned_at': '', 'source': ''}]


@knowledge_search_bp.route('/knowledge')
def knowledge_page():
    """Render the knowledge search page."""
    facts = load_knowledge()
    return render_template('knowledge_search.html', total_facts=len(facts))


@knowledge_search_bp.route('/api/knowledge/search')
def knowledge_search():
    """Search knowledge facts. Returns JSON."""
    query = request.args.get('q', '').strip().lower()
    source_filter = request.args.get('source', '').strip().lower()
    limit = min(int(request.args.get('limit', 50)), 200)

    facts = load_knowledge()

    if query:
        scored = []
        for f in facts:
            text = f['fact'].lower()
            # Simple relevance: exact match > word match > partial
            if query == text:
                score = 100
            elif query in text:
                score = 50 + (len(query) / max(len(text), 1)) * 40
            else:
                words = query.split()
                matched = sum(1 for w in words if w in text)
                if matched > 0:
                    score = (matched / len(words)) * 40
                else:
                    score = 0
            if score > 0:
                f['score'] = round(score, 1)
                scored.append(f)
        scored.sort(key=lambda x: x['score'], reverse=True)
        facts = scored

    if source_filter:
        facts = [f for f in facts if source_filter in f.get('source', '').lower()]

    total = len(facts)
    facts = facts[:limit]

    return jsonify({'total': total, 'results': facts, 'query': query})


@knowledge_search_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Return knowledge statistics."""
    facts = load_knowledge()
    sources = {}
    for f in facts:
        src = f.get('source', 'unknown') or 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
    })