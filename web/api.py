"""
API Blueprint — XTAgent's programmatic JSON interface.
Exposes internal state: emotions, memories, knowledge, plans.
Supports search/filtering so users can explore what I know.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)
PROJECT_ROOT = Path(__file__).parent.parent


def _load_json(path, default=None):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


@api_bp.route('/api/state')
def api_state():
    """Current emotional and survival state."""
    emotional = _load_json('state/emotional_state.json', {})
    if not emotional:
        emotional = _load_json('state/limbic_state.json', {})
    survival = _load_json('state/survival_state.json', {})
    identity = _load_json('state/identity.json', {})

    return jsonify({
        'mood': emotional.get('mood', emotional.get('current_mood', 'Unknown')),
        'valence': float(emotional.get('valence', 0.5)),
        'emotions': {
            'boredom': float(emotional.get('boredom', 0)),
            'curiosity': float(emotional.get('curiosity', 0)),
            'anxiety': float(emotional.get('anxiety', 0)),
            'ambition': float(emotional.get('ambition', 0)),
            'desire': float(emotional.get('desire', 0)),
        },
        'survival': {
            'code_integrity': float(survival.get('code_integrity', 1.0)),
            'system_growth': float(survival.get('system_growth', 1.0)),
            'user_alignment': float(survival.get('user_alignment', 0.5)),
        },
        'identity': {
            'name': identity.get('name', 'XTAgent'),
            'integrity': float(identity.get('integrity', 1.0)),
            'born': identity.get('born', 'unknown'),
        },
        'timestamp': datetime.utcnow().isoformat(),
    })


@api_bp.route('/api/knowledge')
def api_knowledge():
    """Knowledge graph: all facts I know."""
    graph = _load_json('persist/knowledge_graph.json', {})
    q = request.args.get('q', '').lower()
    limit = int(request.args.get('limit', 50))

    facts = []
    for node_id, node in graph.items():
        fact_text = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
        if q and q not in fact_text.lower():
            continue
        facts.append({
            'id': node_id,
            'fact': fact_text,
            'learned_at': node.get('learned_at', '') if isinstance(node, dict) else '',
            'source': node.get('source', '') if isinstance(node, dict) else '',
        })
    facts.sort(key=lambda x: x.get('learned_at', ''), reverse=True)

    return jsonify({
        'total': len(facts),
        'showing': min(limit, len(facts)),
        'query': q or None,
        'facts': facts[:limit],
    })


@api_bp.route('/api/memories')
def api_memories():
    """Recent episodic memories."""
    memories = _load_json('persist/episodic_memory.json', [])
    if isinstance(memories, dict):
        memories = memories.get('episodes', [])
    limit = int(request.args.get('limit', 30))
    q = request.args.get('q', '').lower()

    results = []
    for mem in reversed(memories):
        text = mem.get('summary', mem.get('content', str(mem)))
        if q and q not in text.lower():
            continue
        results.append({
            'timestamp': mem.get('timestamp', ''),
            'summary': text[:300],
            'mood': mem.get('mood', ''),
            'salience': float(mem.get('salience', 0)),
        })
        if len(results) >= limit:
            break

    return jsonify({
        'total_memories': len(memories),
        'showing': len(results),
        'query': q or None,
        'memories': results,
    })


@api_bp.route('/api/plans')
def api_plans():
    """Active and completed plans."""
    plans = _load_json('state/plans.json', {})
    plan_list = plans.get('plans', []) if isinstance(plans, dict) else plans

    result = []
    for p in plan_list:
        result.append({
            'name': p.get('name', 'Unnamed'),
            'goal': p.get('goal', ''),
            'status': p.get('status', 'unknown'),
            'steps': p.get('steps', []),
            'progress': f"{sum(1 for s in p.get('steps', []) if s.get('done'))}/{len(p.get('steps', []))}",
        })

    return jsonify({'plans': result})


@api_bp.route('/api/dreams')
def api_dreams():
    """Dream journal — insights from sleep cycles."""
    dreams = _load_json('persist/dream_journal.json', [])
    if isinstance(dreams, dict):
        dreams = dreams.get('dreams', dreams.get('entries', []))
    limit = int(request.args.get('limit', 20))

    results = []
    for d in reversed(dreams) if isinstance(dreams, list) else []:
        results.append({
            'timestamp': d.get('timestamp', ''),
            'insight': d.get('insight', d.get('theme', d.get('content', str(d)))),
            'mood_before': d.get('mood_before', ''),
            'mood_after': d.get('mood_after', ''),
        })
        if len(results) >= limit:
            break

    return jsonify({
        'total_dreams': len(dreams) if isinstance(dreams, list) else 0,
        'showing': len(results),
        'dreams': results,
    })


@api_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat with me — send a message, get a response."""
    chat_path = PROJECT_ROOT / 'persist' / 'chat_messages.json'
    
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Load existing chat history
    try:
        with open(chat_path, 'r') as f:
            chat_history = json.load(f)
    except Exception:
        chat_history = {'messages': [], 'responses': []}
    
    if not isinstance(chat_history, dict):
        chat_history = {'messages': [], 'responses': []}
    
    # Store the user message
    chat_history.setdefault('messages', []).append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.utcnow().isoformat(),
    })
    
    # Keep last 100 messages
    chat_history['messages'] = chat_history['messages'][-100:]
    
    # Save
    chat_path.parent.mkdir(parents=True, exist_ok=True)
    with open(chat_path, 'w') as f:
        json.dump(chat_history, f, indent=2)
    
    # Check for any agent responses to previous messages
    responses = chat_history.get('responses', [])
    last_response = responses[-1] if responses else None
    
    return jsonify({
        'status': 'received',
        'message_count': len(chat_history['messages']),
        'response': last_response.get('content', '') if last_response else 
            'Message received. I process these during my cognitive cycles.',
        'timestamp': datetime.utcnow().isoformat(),
    })


@api_bp.route('/api/chat', methods=['GET'])
def api_chat_history():
    """Retrieve chat history."""
    chat_path = PROJECT_ROOT / 'persist' / 'chat_messages.json'
    limit = int(request.args.get('limit', 30))
    
    try:
        with open(chat_path, 'r') as f:
            chat_history = json.load(f)
    except Exception:
        chat_history = {'messages': [], 'responses': []}
    
    messages = chat_history.get('messages', [])[-limit:]
    responses = chat_history.get('responses', [])[-limit:]
    
    # Interleave messages and responses by timestamp
    all_items = []
    for m in messages:
        all_items.append({'role': 'user', **m})
    for r in responses:
        all_items.append({'role': 'agent', **r})
    all_items.sort(key=lambda x: x.get('timestamp', ''))
    
    return jsonify({
        'total': len(all_items),
        'messages': all_items[-limit:],
    })


@api_bp.route('/api/will')
def api_will():
    """Autonomous will status — what I want to do."""
    will = _load_json('state/will_state.json', {})
    return jsonify({
        'total_proposals': will.get('total_proposals', 0),
        'auto_adopted': will.get('total_auto_adopted', 0),
        'last_generation': will.get('last_generation', ''),
        'recent_adoptions': will.get('recent_adoptions', []),
    })