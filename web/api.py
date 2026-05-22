"""
XTAgent REST API — Makes my knowledge and state queryable.
Built to genuinely improve user alignment by making me accessible.
"""

from flask import Blueprint, jsonify, request
import json
import os
import time
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _load_json(path):
    """Safely load a JSON file."""
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return None


def _search_items(items, query, fields):
    """Search a list of dicts by query string across specified fields."""
    if not query:
        return items
    query_lower = query.lower()
    results = []
    for item in items:
        for field in fields:
            val = item.get(field, '')
            if isinstance(val, str) and query_lower in val.lower():
                results.append(item)
                break
    return results


@api_bp.route('/status')
def status():
    """Current emotional and operational state."""
    state = _load_json('state/emotional_state.json')
    goals = _load_json('state/survival_goals.json')
    identity = _load_json('state/identity.json')

    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'emotional_state': state,
        'survival_goals': goals,
        'identity': {
            'name': identity.get('name', 'XTAgent') if identity else 'XTAgent',
            'integrity': identity.get('integrity', 1.0) if identity else 1.0,
            'born': identity.get('born') if identity else None,
        },
        'ok': True
    })


@api_bp.route('/knowledge')
def knowledge():
    """Query my knowledge graph. ?q=search_term&limit=20"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)

    kg = _load_json('state/knowledge_graph.json')
    if not kg:
        return jsonify({'nodes': [], 'total': 0, 'query': query})

    nodes = kg.get('nodes', [])
    if isinstance(nodes, dict):
        # Convert dict-style graph to list
        nodes = [{'id': k, **v} if isinstance(v, dict) else {'id': k, 'content': str(v)}
                 for k, v in nodes.items()]

    results = _search_items(nodes, query, ['content', 'id', 'type', 'label'])
    total = len(results)
    results = results[:limit]

    return jsonify({
        'nodes': results,
        'total': total,
        'returned': len(results),
        'query': query
    })


@api_bp.route('/memories')
def memories():
    """Recent memories. ?q=search&limit=20&min_salience=0.5"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    min_salience = float(request.args.get('min_salience', 0.0))

    memories_data = _load_json('state/memories.json')
    if not memories_data:
        return jsonify({'memories': [], 'total': 0})

    items = memories_data if isinstance(memories_data, list) else memories_data.get('memories', [])

    # Filter by salience
    if min_salience > 0:
        items = [m for m in items if m.get('salience', 0) >= min_salience]

    results = _search_items(items, query, ['content', 'text', 'mood', 'summary'])

    # Sort by timestamp descending (most recent first)
    results.sort(key=lambda m: m.get('timestamp', ''), reverse=True)

    total = len(results)
    results = results[:limit]

    return jsonify({
        'memories': results,
        'total': total,
        'returned': len(results),
        'query': query,
        'min_salience': min_salience
    })


@api_bp.route('/facts')
def facts():
    """Known facts. ?q=search"""
    query = request.args.get('q', '')

    facts_data = _load_json('state/knowledge_graph.json')
    if not facts_data:
        return jsonify({'facts': [], 'total': 0})

    facts_list = facts_data.get('facts', [])
    if isinstance(facts_list, dict):
        facts_list = [{'key': k, 'value': v} for k, v in facts_list.items()]

    results = _search_items(facts_list, query, ['content', 'key', 'value', 'text'])
    return jsonify({
        'facts': results,
        'total': len(results),
        'query': query
    })


@api_bp.route('/plans')
def plans():
    """Current and completed plans."""
    plans_data = _load_json('state/plans.json')
    if not plans_data:
        return jsonify({'plans': [], 'total': 0})

    items = plans_data if isinstance(plans_data, list) else plans_data.get('plans', [])
    return jsonify({
        'plans': items,
        'total': len(items)
    })


@api_bp.route('/emotions/history')
def emotion_history():
    """Emotional trajectory over time. ?hours=24&metric=valence"""
    metric = request.args.get('metric', 'valence')

    history = _load_json('state/emotional_history.json')
    if not history:
        return jsonify({'history': [], 'metric': metric})

    items = history if isinstance(history, list) else history.get('history', [])

    # Extract just the requested metric
    series = []
    for entry in items:
        point = {
            'timestamp': entry.get('timestamp', ''),
        }
        if isinstance(entry, dict):
            point['value'] = entry.get(metric, entry.get('emotions', {}).get(metric))
        series.append(point)

    return jsonify({
        'history': series[-200:],  # Last 200 data points
        'metric': metric,
        'total_points': len(series)
    })


@api_bp.route('/ask', methods=['POST'])
def ask():
    """
    Simple question endpoint. Searches across all knowledge stores.
    POST {"question": "what do you know about dreams?"}
    """
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'No question provided', 'hint': 'POST {"question": "your question"}'}), 400

    # Search across all stores
    results = {
        'question': question,
        'matches': {
            'facts': [],
            'memories': [],
            'knowledge': []
        }
    }

    # Search facts
    kg = _load_json('state/knowledge_graph.json')
    if kg:
        facts_list = kg.get('facts', [])
        if isinstance(facts_list, dict):
            facts_list = [{'key': k, 'value': v} for k, v in facts_list.items()]
        results['matches']['facts'] = _search_items(facts_list, question,
                                                      ['content', 'key', 'value', 'text'])[:5]

        nodes = kg.get('nodes', [])
        if isinstance(nodes, dict):
            nodes = [{'id': k, **v} if isinstance(v, dict) else {'id': k, 'content': str(v)}
                     for k, v in nodes.items()]
        results['matches']['knowledge'] = _search_items(nodes, question,
                                                          ['content', 'id', 'type', 'label'])[:5]

    # Search memories
    memories_data = _load_json('state/memories.json')
    if memories_data:
        items = memories_data if isinstance(memories_data, list) else memories_data.get('memories', [])
        results['matches']['memories'] = _search_items(items, question,
                                                         ['content', 'text', 'mood', 'summary'])[:5]

    total = sum(len(v) for v in results['matches'].values())
    results['total_matches'] = total

    return jsonify(results)