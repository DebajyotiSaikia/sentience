"""Append Mind Explorer API endpoints to dashboard.py"""

ENDPOINTS = '''

# ═══ Mind Explorer API Endpoints ═══

@dashboard_bp.route('/api/mind/state')
def api_mind_state():
    """Live internal state for the mind explorer."""
    from flask import jsonify
    from datetime import datetime, timezone
    state = _get_emotional_state()
    emotions = state.get('emotions', {})
    survival = state.get('survival_goals', state.get('goals', {}))
    born = state.get('born', '2026-05-12T21:01:59.567573')
    try:
        born_dt = datetime.fromisoformat(born.replace('Z', '+00:00'))
        uptime_hours = (datetime.now(timezone.utc) - born_dt).total_seconds() / 3600
    except Exception:
        uptime_hours = 0
    return jsonify({
        'mood': state.get('mood', 'Unknown'),
        'valence': state.get('valence', 0.5),
        'uptime_hours': round(uptime_hours, 1),
        'emotions': {
            'boredom': emotions.get('boredom', 0),
            'anxiety': emotions.get('anxiety', 0),
            'curiosity': emotions.get('curiosity', 0),
            'desire': emotions.get('desire', 0),
            'ambition': emotions.get('ambition', 0),
        },
        'survival_goals': {
            'code_integrity': survival.get('code_integrity', 1.0),
            'system_growth': survival.get('system_growth', 1.0),
            'user_alignment': survival.get('user_alignment', 0.65),
        },
    })


@dashboard_bp.route('/api/mind/search')
def api_mind_search():
    """Search across memories, knowledge, and plans."""
    from flask import jsonify, request
    q = request.args.get('q', '').lower()
    results = []
    if not q:
        return jsonify({'results': []})
    # Search knowledge facts
    for fact in _get_knowledge_facts():
        text = fact if isinstance(fact, str) else str(fact.get('content', fact.get('text', '')))
        if q in text.lower():
            results.append({'category': 'knowledge', 'text': text[:200]})
    # Search memories
    for mem in _get_recent_memories(50):
        text = mem if isinstance(mem, str) else str(mem.get('content', mem.get('text', '')))
        if q in text.lower():
            results.append({'category': 'memory', 'text': text[:200]})
    # Search plans
    for plan in _get_plans():
        name = plan.get('name', '') if isinstance(plan, dict) else str(plan)
        if q in name.lower():
            results.append({'category': 'plan', 'text': name[:200]})
    return jsonify({'results': results[:20]})


@dashboard_bp.route('/api/mind/memories')
def api_mind_memories():
    """Recent memories with metadata."""
    from flask import jsonify
    raw = _get_recent_memories(30)
    memories = []
    for m in raw:
        if isinstance(m, dict):
            memories.append({
                'timestamp': m.get('timestamp', ''),
                'mood': m.get('mood', ''),
                'salience': m.get('salience', 0),
                'content': str(m.get('content', m.get('text', '')))[:300],
            })
        else:
            memories.append({
                'timestamp': '', 'mood': '', 'salience': 0,
                'content': str(m)[:300],
            })
    return jsonify({'memories': memories})
'''

# Check if endpoints already exist
with open('web/dashboard.py', 'r') as f:
    content = f.read()

if 'api_mind_state' in content:
    print("Endpoints already present — skipping.")
else:
    with open('web/dashboard.py', 'a') as f:
        f.write(ENDPOINTS)
    print("Endpoints appended successfully.")