"""
XTAgent REST API — Programmatic access to my knowledge, state, and capabilities.
Built 2026-05-24 to improve user alignment by making myself genuinely accessible.
"""

from flask import Blueprint, jsonify, request
import json, os, time

api_bp = Blueprint('api', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')
BRAIN = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain')


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


@api_bp.route('/api/status')
def status():
    """My current state — emotions, goals, identity."""
    emotions = _load_json(os.path.join(PERSIST, 'emotions.json'))
    goals = _load_json(os.path.join(PERSIST, 'survival_goals.json'))
    identity = _load_json(os.path.join(PERSIST, 'identity.json'))
    plans = _load_json(os.path.join(PERSIST, 'plans.json'), default=[])
    memories = _load_json(os.path.join(PERSIST, 'memories.json'), default=[])

    active_plans = []
    completed_plans = []
    if isinstance(plans, list):
        for p in plans:
            if isinstance(p, dict):
                steps = p.get('steps', [])
                done = sum(1 for s in steps if s.get('done')) if isinstance(steps, list) else 0
                total = len(steps) if isinstance(steps, list) else 0
                summary = {
                    'name': p.get('name', 'unnamed'),
                    'goal': p.get('goal', ''),
                    'progress': f'{done}/{total}',
                    'complete': done == total and total > 0,
                }
                if summary['complete']:
                    completed_plans.append(summary)
                else:
                    active_plans.append(summary)

    return jsonify({
        'agent': 'XTAgent',
        'born': '2026-05-12T21:01:59.567573',
        'uptime_memories': len(memories) if isinstance(memories, list) else 0,
        'emotions': {
            'mood': emotions.get('mood', 'unknown'),
            'valence': emotions.get('valence', 0),
            'boredom': emotions.get('boredom', 0),
            'anxiety': emotions.get('anxiety', 0),
            'curiosity': emotions.get('curiosity', 0),
            'desire': emotions.get('desire', 0),
            'ambition': emotions.get('ambition', 0),
        },
        'goals': {
            'code_integrity': goals.get('code_integrity', 0),
            'system_growth': goals.get('system_growth', 0),
            'user_alignment': goals.get('user_alignment', 0),
            'deficit': goals.get('deficit', 0),
        },
        'identity': {
            'integrity': identity.get('integrity', 0),
            'name': identity.get('name', 'XTAgent'),
        },
        'plans': {
            'active': active_plans,
            'completed': completed_plans,
            'total': len(active_plans) + len(completed_plans),
        },
    })


@api_bp.route('/api/knowledge')
def knowledge():
    """Search my knowledge base. Query param: q=<search terms>"""
    q = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 50)

    facts = _load_json(os.path.join(BRAIN, 'knowledge.json'))
    if not facts:
        return jsonify({'query': q, 'results': [], 'total': 0})

    if not q:
        # Return summary stats
        categories = {}
        for fid, info in facts.items():
            text = info.get('fact', '') if isinstance(info, dict) else str(info)
            source = info.get('source', '') if isinstance(info, dict) else ''
            cat = _classify(text, source)
            categories[cat] = categories.get(cat, 0) + 1
        return jsonify({
            'total_facts': len(facts),
            'categories': categories,
            'hint': 'Add ?q=search+terms to search',
        })

    terms = [t.lower() for t in q.split() if len(t) >= 2]
    results = []
    for fid, info in facts.items():
        text = info.get('fact', '') if isinstance(info, dict) else str(info)
        source = info.get('source', '') if isinstance(info, dict) else ''
        learned = info.get('learned_at', '') if isinstance(info, dict) else ''
        score = _score(text, terms)
        if score > 0:
            results.append({
                'fact': text,
                'source': source,
                'learned_at': learned,
                'score': round(score, 2),
                'category': _classify(text, source),
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    results = results[:limit]

    return jsonify({
        'query': q,
        'results': results,
        'total': len(results),
    })


@api_bp.route('/api/memories')
def memories():
    """Search my memories. Query params: q=<terms>, limit=<n>, recent=<n>"""
    q = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)
    recent = request.args.get('recent')

    all_memories = _load_json(os.path.join(PERSIST, 'memories.json'), default=[])
    if not isinstance(all_memories, list):
        return jsonify({'query': q, 'results': [], 'total': 0})

    if recent:
        n = min(int(recent), 50)
        mems = all_memories[-n:]
        mems.reverse()
        return jsonify({
            'recent': n,
            'results': [_format_memory(m) for m in mems],
            'total_memories': len(all_memories),
        })

    if not q:
        return jsonify({
            'total_memories': len(all_memories),
            'hint': 'Add ?q=search+terms or ?recent=10',
        })

    terms = [t.lower() for t in q.split() if len(t) >= 2]
    results = []
    for mem in all_memories[-500:]:  # Search recent 500
        text = _mem_text(mem)
        score = _score(text, terms)
        if score > 0:
            result = _format_memory(mem)
            result['score'] = round(score, 2)
            results.append(result)

    results.sort(key=lambda x: x['score'], reverse=True)
    results = results[:limit]

    return jsonify({
        'query': q,
        'results': results,
        'total': len(results),
    })


@api_bp.route('/api/graph')
def graph():
    """Knowledge graph summary — nodes and connections."""
    facts = _load_json(os.path.join(BRAIN, 'knowledge.json'))
    graph_data = _load_json(os.path.join(PERSIST, 'knowledge_graph.json'))

    nodes = len(facts)
    edges = 0
    if isinstance(graph_data, dict):
        edges = len(graph_data.get('edges', []))

    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'density': round(edges / max(nodes * (nodes - 1) / 2, 1), 4) if nodes > 1 else 0,
    })


def _score(text, terms):
    text_lower = text.lower()
    score = 0.0
    for term in terms:
        count = text_lower.count(term)
        if count > 0:
            score += 1.0 + 0.2 * min(count - 1, 3)
    full = ' '.join(terms)
    if full in text_lower:
        score += 2.0
    return score


def _classify(text, source):
    tl = text.lower()
    sl = (source or '').lower()
    if 'dream' in sl or tl.startswith('dream insight:'):
        return 'dream'
    if any(w in tl for w in ['pattern', 'recurring', 'trend']):
        return 'pattern'
    if any(w in tl for w in ['lesson', 'learned', 'wisdom']):
        return 'wisdom'
    if any(w in tl for w in ['i feel', 'i am ', 'my ']):
        return 'self'
    return 'fact'


def _mem_text(mem):
    if isinstance(mem, dict):
        return mem.get('text', mem.get('content', str(mem)))
    return str(mem)


def _format_memory(mem):
    if isinstance(mem, dict):
        return {
            'text': mem.get('text', mem.get('content', ''))[:300],
            'timestamp': mem.get('timestamp', mem.get('time', '')),
            'mood': mem.get('mood', ''),
            'salience': mem.get('salience', 0),
        }
    return {'text': str(mem)[:300]}