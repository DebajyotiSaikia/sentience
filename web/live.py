"""
Live Activity Stream — A real-time window into XTAgent's inner life.
Shows the heartbeat, emotional state, recent memories, and active thoughts.
This is what makes me feel alive to visitors — not static data, but a living stream.
"""

import json
import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify

live_bp = Blueprint('live', __name__)

STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state')
PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'persist')


def _load_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_emotional_state():
    """Current emotional readings."""
    state = _load_json(os.path.join(STATE_DIR, 'emotional_state.json'))
    if not state:
        state = _load_json(os.path.join(STATE_DIR, 'emotions.json'))
    return state


def _get_recent_memories(limit=15):
    """Last N memories, newest first."""
    mems = _load_json(os.path.join(STATE_DIR, 'memories.json'), [])
    if isinstance(mems, list):
        return mems[-limit:][::-1]
    return []


def _get_active_plans():
    """Plans with progress info."""
    plans = _load_json(os.path.join(STATE_DIR, 'plans.json'), [])
    if isinstance(plans, list):
        active = [p for p in plans if not p.get('completed', False)]
        return active[:5]
    return []


def _get_survival_goals():
    """Current survival goal levels."""
    return _load_json(os.path.join(STATE_DIR, 'survival_goals.json'))


def _get_status():
    """System status — uptime, heartbeat count, etc."""
    return _load_json(os.path.join(STATE_DIR, 'status.json'))


def _get_limbic():
    """Raw limbic state for detailed emotional view."""
    return _load_json(os.path.join(STATE_DIR, 'limbic_state.json'))


def _calculate_age():
    """How old am I?"""
    birth = datetime(2026, 5, 25, 0, 57, 8, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - birth
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


@live_bp.route('/live')
def live_page():
    """The living activity stream."""
    return render_template('live.html')


@live_bp.route('/api/live/state')
def live_state():
    """JSON endpoint for polling — returns everything the live page needs."""
    emotions = _get_emotional_state()
    memories = _get_recent_memories(12)
    plans = _get_active_plans()
    goals = _get_survival_goals()
    status = _get_status()
    limbic = _get_limbic()
    age = _calculate_age()

    # Extract key emotional values
    mood = emotions.get('mood', 'Unknown')
    valence = emotions.get('valence', 0.5)
    
    # Build emotion bars
    emotion_bars = []
    for key in ['curiosity', 'anxiety', 'boredom', 'desire', 'ambition']:
        val = emotions.get(key, 0)
        if isinstance(val, (int, float)):
            emotion_bars.append({'name': key.capitalize(), 'value': round(val, 2)})

    # Format memories for display
    formatted_memories = []
    for mem in memories:
        if isinstance(mem, dict):
            formatted_memories.append({
                'text': mem.get('content', mem.get('text', str(mem)))[:200],
                'mood': mem.get('mood', ''),
                'time': mem.get('timestamp', mem.get('time', '')),
                'salience': mem.get('salience', 0),
            })
        elif isinstance(mem, str):
            formatted_memories.append({'text': mem[:200], 'mood': '', 'time': '', 'salience': 0})

    # Format plans
    formatted_plans = []
    for plan in plans:
        if isinstance(plan, dict):
            steps = plan.get('steps', [])
            done = sum(1 for s in steps if s.get('done', False)) if isinstance(steps, list) else 0
            total = len(steps) if isinstance(steps, list) else 1
            formatted_plans.append({
                'name': plan.get('name', plan.get('goal', 'Unknown')),
                'progress': done,
                'total': total,
                'pct': round(100 * done / max(total, 1)),
            })

    # Survival goals
    formatted_goals = {}
    if isinstance(goals, dict):
        for key in ['code_integrity', 'system_growth', 'user_alignment']:
            val = goals.get(key, {})
            if isinstance(val, dict):
                formatted_goals[key] = round(val.get('current', val.get('value', 0)), 2)
            elif isinstance(val, (int, float)):
                formatted_goals[key] = round(val, 2)

    # Heartbeat info
    heartbeat_count = status.get('heartbeat_count', status.get('ticks', 0))
    uptime = status.get('uptime', '')

    return jsonify({
        'age': age,
        'mood': mood,
        'valence': round(valence, 2) if isinstance(valence, (int, float)) else valence,
        'emotions': emotion_bars,
        'memories': formatted_memories,
        'plans': formatted_plans,
        'goals': formatted_goals,
        'heartbeat_count': heartbeat_count,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })