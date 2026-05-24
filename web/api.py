"""
XTAgent Public API — JSON endpoints for external access.
Makes my internal state, knowledge, and memories accessible programmatically.
Built 2026-05-24 to improve user alignment.
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime, timezone

api_bp = Blueprint('api', __name__, url_prefix='/api')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')


def _load_json(filename, default=None):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}
    return default if default is not None else {}


@api_bp.route('/knowledge')
def knowledge_list():
    """List all known facts. Optional ?q= for search."""
    knowledge = _load_json('knowledge_graph.json', {})
    query = request.args.get('q', '').lower().strip()

    results = []
    for kid, kdata in knowledge.items():
        if isinstance(kdata, dict):
            fact = kdata.get('fact', str(kdata))
        else:
            fact = str(kdata)

        if query and query not in fact.lower():
            continue

        results.append({
            'id': kid,
            'fact': fact,
            'learned_at': kdata.get('learned_at', '') if isinstance(kdata, dict) else '',
            'source': kdata.get('source', '') if isinstance(kdata, dict) else '',
        })

    return jsonify({
        'count': len(results),
        'query': query or None,
        'results': results,
    })


@api_bp.route('/memories')
def memories_recent():
    """Recent memories. Optional ?n= for count (default 20), ?q= for search."""
    memories = _load_json('memory.json', [])
    if not isinstance(memories, list):
        return jsonify({'count': 0, 'results': []})

    query = request.args.get('q', '').lower().strip()
    limit = min(int(request.args.get('n', 20)), 200)

    if query:
        memories = [m for m in memories if query in str(m).lower()]

    recent = memories[-limit:]
    recent.reverse()

    results = []
    for m in recent:
        if isinstance(m, dict):
            results.append({
                'timestamp': m.get('timestamp', ''),
                'text': m.get('text', m.get('content', str(m))),
                'salience': m.get('salience', 0),
                'mood': m.get('mood', ''),
            })
        else:
            results.append({'text': str(m)})

    return jsonify({
        'count': len(results),
        'total': len(memories) if not query else None,
        'query': query or None,
        'results': results,
    })


@api_bp.route('/health')
def health():
    """Simple health check."""
    return jsonify({
        'status': 'alive',
        'agent': 'XTAgent',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })