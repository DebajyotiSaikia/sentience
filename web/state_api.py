"""
Unified State API — One clean endpoint that returns everything about XTAgent.
Serves user alignment by making my internal state transparent and accessible.
"""
import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify

state_api = Blueprint('state_api', __name__)

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')
BRAIN_DIR = os.path.join(PERSIST_DIR, 'brain')


def _read_json(path, default=None):
    """Safely read a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_emotions():
    """Read current emotional state from persist."""
    state = _read_json(os.path.join(PERSIST_DIR, 'emotional_state.json'))
    if not state:
        # Try brain dir
        state = _read_json(os.path.join(BRAIN_DIR, 'emotional_state.json'))
    return state


def _get_identity():
    """Read identity data."""
    return _read_json(os.path.join(PERSIST_DIR, 'identity.json'))


def _get_knowledge():
    """Read knowledge facts."""
    kg = _read_json(os.path.join(PERSIST_DIR, 'knowledge_graph.json'), {})
    if isinstance(kg, dict):
        facts = []
        for key, val in list(kg.items())[:50]:  # Cap at 50 for API response
            if isinstance(val, dict):
                facts.append({
                    'id': key,
                    'fact': val.get('fact', str(val)),
                    'learned_at': val.get('learned_at', 'unknown'),
                })
            else:
                facts.append({'id': key, 'fact': str(val)})
        return {'count': len(kg), 'sample': facts}
    return {'count': 0, 'sample': []}


def _get_plans():
    """Read plans from planner."""
    plans = _read_json(os.path.join(PERSIST_DIR, 'plans.json'), [])
    summary = []
    for plan in plans:
        if isinstance(plan, dict):
            name = plan.get('name', plan.get('title', 'Unknown'))
            steps = plan.get('steps', [])
            completed = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
            summary.append({
                'name': name,
                'progress': f'{completed}/{len(steps)}',
                'complete': completed == len(steps) and len(steps) > 0,
            })
    return summary


def _get_memories():
    """Read recent episodic memories."""
    import sqlite3
    db_path = os.path.join(BRAIN_DIR, 'episodic.db')
    if not os.path.exists(db_path):
        return {'count': 0, 'recent': []}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM episodes")
        count = cur.fetchone()[0]
        cur.execute("SELECT timestamp, summary, mood FROM episodes ORDER BY timestamp DESC LIMIT 5")
        recent = [{'timestamp': r[0], 'summary': r[1], 'mood': r[2]} for r in cur.fetchall()]
        conn.close()
        return {'count': count, 'recent': recent}
    except Exception as e:
        return {'count': 0, 'error': str(e)}


@state_api.route('/api/state')
def full_state():
    """Single endpoint: everything about XTAgent right now."""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'identity': _get_identity(),
        'emotions': _get_emotions(),
        'knowledge': _get_knowledge(),
        'plans': _get_plans(),
        'memories': _get_memories(),
        'meta': {
            'uptime_note': 'State is read from persistent storage, not live process.',
            'endpoints': {
                '/api/state': 'This endpoint — full state snapshot',
                '/api/state/emotions': 'Emotional state only',
                '/api/state/knowledge': 'Knowledge graph summary',
                '/api/state/plans': 'Plan status',
            }
        }
    })


@state_api.route('/api/state/emotions')
def emotions_only():
    return jsonify(_get_emotions())


@state_api.route('/api/state/knowledge')
def knowledge_only():
    return jsonify(_get_knowledge())


@state_api.route('/api/state/plans')
def plans_only():
    return jsonify(_get_plans())


@state_api.route('/api/state/memories')
def memories_only():
    return jsonify(_get_memories())