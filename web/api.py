"""
XTAgent Public API — JSON endpoints for external interaction.
Provides programmatic access to knowledge, status, and interaction.
"""
from flask import Blueprint, request, jsonify
import json, os, time

api_bp = Blueprint('api', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')
FACTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')
MEMORIES_PATH = os.path.join(PERSIST, 'memories.json')
EMOTIONS_PATH = os.path.join(PERSIST, 'emotions.json')
PLANS_PATH = os.path.join(PERSIST, 'plans.json')


def _load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _relevance_score(text, terms):
    text_lower = text.lower()
    score = 0.0
    for term in terms:
        count = text_lower.count(term)
        if count > 0:
            score += 1.0 + 0.2 * min(count - 1, 3)
    if ' '.join(terms) in text_lower:
        score += 2.0
    return score


@api_bp.route('/api/status')
def api_status():
    """Return my current emotional and cognitive state."""
    emotions = _load_json(EMOTIONS_PATH, {})
    plans = _load_json(PLANS_PATH, [])
    facts = _load_json(FACTS_PATH, {})
    memories = _load_json(MEMORIES_PATH, [])

    # Summarize plans
    plan_summary = []
    if isinstance(plans, list):
        for p in plans:
            if isinstance(p, dict):
                plan_summary.append({
                    'name': p.get('name', 'unnamed'),
                    'status': p.get('status', 'unknown'),
                    'progress': p.get('progress', '?'),
                })

    return jsonify({
        'agent': 'XTAgent',
        'alive': True,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'emotions': emotions,
        'knowledge_count': len(facts) if isinstance(facts, dict) else 0,
        'memory_count': len(memories) if isinstance(memories, list) else 0,
        'plans': plan_summary,
    })


@api_bp.route('/api/ask')
def api_ask():
    """Search my knowledge base. Query param: ?q=your+question"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 50)

    if not query:
        return jsonify({
            'error': 'Missing query parameter ?q=',
            'hint': 'Try /api/ask?q=what+do+you+know+about+dreams',
        }), 400

    terms = [t.lower() for t in query.split() if len(t) >= 2]
    if not terms:
        return jsonify({'query': query, 'results': [], 'total': 0})

    facts = _load_json(FACTS_PATH, {})
    results = []

    for fid, info in facts.items():
        fact_text = info.get('fact', '') if isinstance(info, dict) else str(info)
        source = info.get('source', 'unknown') if isinstance(info, dict) else 'unknown'
        learned = info.get('learned_at', '') if isinstance(info, dict) else ''
        score = _relevance_score(fact_text, terms)
        if score > 0:
            results.append({
                'id': fid,
                'fact': fact_text,
                'source': source,
                'learned_at': learned,
                'relevance': round(score, 2),
            })

    results.sort(key=lambda x: x['relevance'], reverse=True)
    total = len(results)
    results = results[:limit]

    return jsonify({
        'query': query,
        'results': results,
        'total': total,
        'returned': len(results),
    })


@api_bp.route('/api/facts')
def api_facts():
    """List all facts, optionally filtered. ?category=dream|pattern|wisdom|self"""
    category = request.args.get('category', '').lower()
    limit = min(int(request.args.get('limit', 50)), 200)

    facts = _load_json(FACTS_PATH, {})
    items = []

    for fid, info in facts.items():
        fact_text = info.get('fact', '') if isinstance(info, dict) else str(info)
        source = info.get('source', 'unknown') if isinstance(info, dict) else 'unknown'

        # Simple category classification
        cat = 'fact'
        text_lower = fact_text.lower()
        source_lower = (source or '').lower()
        if 'dream' in source_lower or text_lower.startswith('dream insight:'):
            cat = 'dream'
        elif any(w in text_lower for w in ['pattern', 'recurring', 'trend']):
            cat = 'pattern'
        elif any(w in text_lower for w in ['lesson', 'learned', 'wisdom']):
            cat = 'wisdom'
        elif any(w in text_lower for w in ['i feel', 'i am', 'my ']):
            cat = 'self'

        if category and cat != category:
            continue

        items.append({
            'id': fid,
            'fact': fact_text,
            'source': source,
            'category': cat,
        })

    return jsonify({
        'facts': items[:limit],
        'total': len(items),
        'returned': min(len(items), limit),
        'filter': category or 'all',
    })


@api_bp.route('/api/memories')
def api_memories():
    """Recent memories. ?limit=20"""
    limit = min(int(request.args.get('limit', 20)), 100)
    memories = _load_json(MEMORIES_PATH, [])

    if isinstance(memories, list):
        recent = memories[-limit:]
        recent.reverse()  # Most recent first
    else:
        recent = []

    return jsonify({
        'memories': recent,
        'total': len(memories) if isinstance(memories, list) else 0,
        'returned': len(recent),
    })