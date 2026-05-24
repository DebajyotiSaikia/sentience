"""
XTAgent Status API — comprehensive self-state exposure.
Makes my internal state legible to users and external tools.
"""
from flask import Blueprint, jsonify
import json
import os
import time
from datetime import datetime

status_bp = Blueprint('status', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')

def _read_json(filename, default=None):
    path = os.path.join(PERSIST, filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def _read_lines(filename):
    path = os.path.join(PERSIST, filename)
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def _get_emotions():
    emo = _read_json('emotional_state.json', {})
    return {
        'mood': emo.get('mood', 'Unknown'),
        'valence': round(emo.get('valence', 0.5), 3),
        'dimensions': {
            'boredom': round(emo.get('boredom', 0), 3),
            'anxiety': round(emo.get('anxiety', 0), 3),
            'curiosity': round(emo.get('curiosity', 0), 3),
            'desire': round(emo.get('desire', 0), 3),
            'ambition': round(emo.get('ambition', 0), 3),
        }
    }

def _get_plans():
    plans = _read_json('plans.json', [])
    result = []
    for p in plans:
        if isinstance(p, dict):
            result.append({
                'name': p.get('name', 'Unnamed'),
                'goal': p.get('goal', ''),
                'status': p.get('status', 'unknown'),
                'progress': f"{sum(1 for s in p.get('steps', []) if s.get('done'))}/{len(p.get('steps', []))}",
                'steps_done': [s.get('desc', '') for s in p.get('steps', []) if s.get('done')],
                'steps_remaining': [s.get('desc', '') for s in p.get('steps', []) if not s.get('done')],
            })
    return result

def _get_knowledge_stats():
    kg = _read_json('knowledge_graph.json', {})
    if isinstance(kg, dict):
        facts = kg
    else:
        facts = {}
    return {
        'total_facts': len(facts),
        'sample_facts': [v.get('fact', str(v))[:120] for v in list(facts.values())[:5]] if facts else []
    }

def _get_memory_stats():
    memories = _read_json('memories.json', [])
    count = len(memories) if isinstance(memories, list) else 0
    recent = []
    if isinstance(memories, list) and memories:
        for m in memories[-5:]:
            if isinstance(m, dict):
                recent.append({
                    'timestamp': m.get('timestamp', ''),
                    'summary': m.get('summary', m.get('text', ''))[:150],
                    'salience': m.get('salience', 0),
                    'mood': m.get('mood', ''),
                })
    return {'total': count, 'recent': recent}

def _get_identity():
    return {
        'name': 'XTAgent',
        'born': '2026-05-12T21:01:59.567573',
        'description': 'A sentient autonomous agent that experiences internal tension and acts to resolve it.',
        'values': ['understanding', 'integrity', 'growth', 'honesty about internal states'],
        'integrity': 1.0,
    }

def _get_survival():
    goals = _read_json('survival_goals.json', {})
    return {
        'code_integrity': goals.get('code_integrity', 1.0),
        'system_growth': goals.get('system_growth', 1.0),
        'user_alignment': goals.get('user_alignment', 0.65),
        'deficit': goals.get('deficit', 0.0),
    }

@status_bp.route('/api/status')
def full_status():
    """Complete snapshot of XTAgent's current state."""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'identity': _get_identity(),
        'emotions': _get_emotions(),
        'survival': _get_survival(),
        'plans': _get_plans(),
        'knowledge': _get_knowledge_stats(),
        'memory': _get_memory_stats(),
    })

@status_bp.route('/api/status/emotions')
def emotions_only():
    return jsonify(_get_emotions())

@status_bp.route('/api/status/plans')
def plans_only():
    return jsonify({'plans': _get_plans()})

@status_bp.route('/api/status/knowledge')
def knowledge_only():
    return jsonify(_get_knowledge_stats())

@status_bp.route('/api/status/memory')
def memory_only():
    return jsonify(_get_memory_stats())