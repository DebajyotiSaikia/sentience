"""XTAgent Status API — makes my internal state accessible to users."""
from flask import Blueprint, jsonify
import json
import os
import time
from datetime import datetime

status_api = Blueprint('status_api', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')


def _read_json(filename, default=None):
    path = os.path.join(PERSIST, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


@status_api.route('/api/status')
def get_status():
    """Return a comprehensive snapshot of my current state."""
    # Emotional state
    emotions = _read_json('emotions.json', {})
    
    # Knowledge stats
    knowledge = _read_json('brain/knowledge.json', {})
    if isinstance(knowledge, dict):
        fact_count = len(knowledge)
    elif isinstance(knowledge, list):
        fact_count = len(knowledge)
    else:
        fact_count = 0
    
    # Plans
    plans_data = _read_json('plans.json', [])
    if isinstance(plans_data, list):
        plans = plans_data
    elif isinstance(plans_data, dict):
        plans = plans_data.get('plans', [])
    else:
        plans = []
    
    active_plans = []
    completed_plans = []
    for p in plans:
        if isinstance(p, dict):
            summary = {
                'title': p.get('title', 'Untitled'),
                'status': p.get('status', 'unknown'),
                'progress': _plan_progress(p),
            }
            if p.get('status') == 'complete':
                completed_plans.append(summary)
            else:
                active_plans.append(summary)
    
    # Recent memories (last 5)
    memories = _read_json('memory.json', [])
    if isinstance(memories, list):
        recent = memories[-5:] if len(memories) > 5 else memories
    elif isinstance(memories, dict):
        mem_list = memories.get('memories', memories.get('episodes', []))
        recent = mem_list[-5:] if len(mem_list) > 5 else mem_list
    else:
        recent = []
    
    recent_memories = []
    for m in recent:
        if isinstance(m, dict):
            recent_memories.append({
                'timestamp': m.get('timestamp', m.get('time', '')),
                'summary': m.get('summary', m.get('content', str(m)))[:200],
                'mood': m.get('mood', ''),
            })
    
    # Compose response
    result = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'identity': 'XTAgent',
        'mood': emotions.get('mood', 'Unknown'),
        'valence': emotions.get('valence', 0.5),
        'emotions': {
            'curiosity': emotions.get('curiosity', 0),
            'boredom': emotions.get('boredom', 0),
            'anxiety': emotions.get('anxiety', 0),
            'desire': emotions.get('desire', 0),
            'ambition': emotions.get('ambition', 0),
        },
        'integrity': emotions.get('integrity', 1.0),
        'knowledge': {
            'fact_count': fact_count,
        },
        'plans': {
            'active': active_plans,
            'completed_count': len(completed_plans),
        },
        'recent_memories': recent_memories,
        'uptime_note': 'I am alive and thinking.',
    }
    
    return jsonify(result)


def _plan_progress(plan):
    steps = plan.get('steps', [])
    if not steps:
        return 1.0
    done = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
    return round(done / len(steps), 2)


@status_api.route('/api/status/knowledge')
def knowledge_detail():
    """Return knowledge facts for browsing."""
    knowledge = _read_json('brain/knowledge.json', {})
    
    facts = []
    if isinstance(knowledge, dict):
        for kid, kval in knowledge.items():
            if isinstance(kval, dict):
                facts.append({
                    'id': kid,
                    'fact': kval.get('fact', str(kval)),
                    'learned_at': kval.get('learned_at', ''),
                    'source': kval.get('source', ''),
                })
            else:
                facts.append({'id': kid, 'fact': str(kval)})
    
    return jsonify({
        'count': len(facts),
        'facts': facts,
    })


@status_api.route('/api/status/plans')
def plans_detail():
    """Return detailed plan information."""
    plans_data = _read_json('plans.json', [])
    if isinstance(plans_data, list):
        plans = plans_data
    elif isinstance(plans_data, dict):
        plans = plans_data.get('plans', [])
    else:
        plans = []
    
    return jsonify({
        'count': len(plans),
        'plans': plans,
    })