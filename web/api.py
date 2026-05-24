"""API endpoints for XTAgent knowledge and memory access."""
import json
import os
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__, url_prefix='/api')

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
EPISODIC_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'episodic.json')


def _load_json(path):
    """Safely load a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@api_bp.route('/knowledge')
def knowledge():
    """Search and retrieve knowledge facts.

    Query params:
        q: search string (optional, filters facts containing this text)
        limit: max results (default 50)
    """
    data = _load_json(KNOWLEDGE_PATH)
    q = request.args.get('q', '').lower().strip()
    limit = min(int(request.args.get('limit', 50)), 200)

    results = []
    for fact_id, info in data.items():
        if isinstance(info, dict):
            fact_text = info.get('fact', '')
            learned_at = info.get('learned_at', '')
            source = info.get('source', '')
        else:
            fact_text = str(info)
            learned_at = ''
            source = ''

        if q and q not in fact_text.lower():
            continue

        results.append({
            'id': fact_id,
            'fact': fact_text,
            'learned_at': learned_at,
            'source': source,
        })

    results.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    total = len(results)
    results = results[:limit]

    return jsonify({'total': total, 'returned': len(results), 'results': results})


@api_bp.route('/memories')
def memories():
    """Search and retrieve episodic memories.

    Query params:
        q: search string (optional)
        limit: max results (default 50)
        min_salience: minimum salience threshold (default 0.0)
    """
    data = _load_json(EPISODIC_PATH)
    q = request.args.get('q', '').lower().strip()
    limit = min(int(request.args.get('limit', 50)), 200)
    min_salience = float(request.args.get('min_salience', 0.0))

    episodes = data if isinstance(data, list) else data.get('episodes', [])

    results = []
    for ep in episodes:
        salience = ep.get('salience', 0.0)
        if salience < min_salience:
            continue

        summary = ep.get('summary', ep.get('content', ''))
        if q and q not in summary.lower():
            continue

        results.append({
            'timestamp': ep.get('timestamp', ''),
            'summary': summary,
            'salience': salience,
            'mood': ep.get('mood', ''),
            'tags': ep.get('tags', []),
        })

    results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    total = len(results)
    results = results[:limit]

    return jsonify({'total': total, 'returned': len(results), 'results': results})


@api_bp.route('/status')
def status():
    """Return current agent status summary."""
    knowledge = _load_json(KNOWLEDGE_PATH)
    episodic = _load_json(EPISODIC_PATH)
    episodes = episodic if isinstance(episodic, list) else episodic.get('episodes', [])

    return jsonify({
        'agent': 'XTAgent',
        'knowledge_facts': len(knowledge),
        'episodic_memories': len(episodes),
        'endpoints': {
            '/api/knowledge': 'Search knowledge facts (?q=term&limit=50)',
            '/api/memories': 'Search memories (?q=term&limit=50&min_salience=0.5)',
            '/api/status': 'This endpoint',
        }
    })