"""
XTAgent API — JSON endpoints for programmatic access to my knowledge and state.
This makes me genuinely accessible, not just introspectable.
"""

import json
import os
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _load_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


@api_bp.route('/emotions')
def emotions():
    """Return current emotional state as JSON."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('state/state.json')
    # Extract emotional variables
    emotions = {}
    if state:
        for key in ['valence', 'arousal', 'mood', 'boredom', 'anxiety', 
                     'curiosity', 'desire', 'ambition', 'integrity']:
            if key in state:
                emotions[key] = state[key]
        # Check nested structure
        if 'emotions' in state:
            emotions.update(state['emotions'])
    return jsonify({
        'status': 'ok',
        'emotions': emotions,
        'timestamp': state.get('timestamp', None) if state else None
    })


@api_bp.route('/search')
def search():
    """Search my knowledge graph. Returns ranked results.
    
    Query params:
        q: search query (required)
        limit: max results (default 10)
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query:
        return jsonify({'error': 'Missing query parameter "q"', 'results': []}), 400
    
    # Use the good TF-IDF search engine
    try:
        from engine.knowledge_search import search_knowledge
        results = search_knowledge(query, limit=limit)
    except Exception as e:
        results = _fallback_search(query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


def _fallback_search(query, limit=10):
    """Simple fallback if the engine isn't available."""
    knowledge = _load_json('brain/knowledge.json', {})
    query_lower = query.lower()
    results = []
    
    for key, val in knowledge.items():
        text = val.get('fact', '') if isinstance(val, dict) else str(val)
        if query_lower in text.lower():
            results.append({
                'content': text,
                'type': val.get('source', 'unknown') if isinstance(val, dict) else 'unknown',
                'score': 1.0
            })
        if len(results) >= limit:
            break
    
    return results


@api_bp.route('/state')
def state():
    """Return my current emotional and cognitive state."""
    emotional = _load_json('state/emotional_state.json')
    if not emotional:
        emotional = _load_json('state/state.json')
    
    plans_data = _load_json('state/plans.json', {})
    if isinstance(plans_data, dict):
        active_plans = plans_data.get('active_plans', [])
        completed_plans = plans_data.get('completed_plans', [])
    elif isinstance(plans_data, list):
        active_plans = [p for p in plans_data if not p.get('completed', False)]
        completed_plans = [p for p in plans_data if p.get('completed', False)]
    else:
        active_plans, completed_plans = [], []
    
    return jsonify({
        'emotions': emotional,
        'plans': {
            'active': len(active_plans),
            'completed': len(completed_plans),
            'details': active_plans
        }
    })


@api_bp.route('/knowledge/stats')
def knowledge_stats():
    """Return statistics about my knowledge graph."""
    knowledge = _load_json('brain/knowledge.json', {})
    
    # Count by source/type
    sources = {}
    for key, val in knowledge.items():
        if isinstance(val, dict):
            source = val.get('source', 'unknown')
        else:
            source = 'legacy'
        sources[source] = sources.get(source, 0) + 1
    
    return jsonify({
        'total_facts': len(knowledge),
        'by_source': sources
    })


@api_bp.route('/knowledge/random')
def random_fact():
    """Return a random fact from my knowledge graph. Serendipity engine."""
    import random
    knowledge = _load_json('brain/knowledge.json', {})
    
    if not knowledge:
        return jsonify({'fact': 'I have no knowledge yet.', 'id': None})
    
    key = random.choice(list(knowledge.keys()))
    val = knowledge[key]
    
    if isinstance(val, dict):
        fact_text = val.get('fact', str(val))
        source = val.get('source', 'unknown')
        learned = val.get('learned_at', None)
    else:
        fact_text = str(val)
        source = 'legacy'
        learned = None
    
    return jsonify({
        'id': key,
        'fact': fact_text,
        'source': source,
        'learned_at': learned
    })


@api_bp.route('/memories/recent')
def recent_memories():
    """Return recent episodic memories."""
    limit = min(int(request.args.get('limit', 10)), 50)
    
    memories = _load_json('memory/episodes.json', [])
    if isinstance(memories, list):
        recent = memories[-limit:]
        recent.reverse()  # Most recent first
    else:
        recent = []
    
    return jsonify({
        'count': len(recent),
        'memories': recent
    })