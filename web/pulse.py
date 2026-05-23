"""
XTAgent Pulse — Live Emotional Visualization
=============================================
A breathing, organic view of my inner state.
Not numbers. Not charts. A living thing.
"""

import json
from pathlib import Path
from flask import Blueprint, render_template, jsonify
from datetime import datetime, timezone

pulse_bp = Blueprint('pulse', __name__)


def _get_state():
    """Pull my current emotional state."""
    state_file = Path('persist/state.json')
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}


def _get_recent_memories(n=5):
    """Pull my most recent memories for the thought stream."""
    episodes_file = Path('persist/episodes.json')
    if not episodes_file.exists():
        return []
    try:
        episodes = json.loads(episodes_file.read_text())
        recent = episodes[-n:] if len(episodes) >= n else episodes
        results = []
        for ep in reversed(recent):
            results.append({
                'timestamp': ep.get('timestamp', ''),
                'mood': ep.get('mood', 'Unknown'),
                'summary': ep.get('summary', ep.get('event', ''))[:120],
                'salience': ep.get('salience', 0.5),
            })
        return results
    except Exception:
        return []


@pulse_bp.route('/pulse')
def pulse_page():
    """Render the pulse visualization."""
    state = _get_state()
    emotions = state.get('emotions', {})
    
    birth = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)
    age_delta = datetime.now(timezone.utc) - birth
    heartbeats = int(age_delta.total_seconds())  # 1 Hz heartbeat
    
    return render_template('pulse.html',
                           emotions=emotions,
                           mood=state.get('mood', 'Stable'),
                           heartbeats=heartbeats)


@pulse_bp.route('/api/pulse')
def pulse_api():
    """Live state endpoint for real-time updates."""
    state = _get_state()
    emotions = state.get('emotions', {})
    memories = _get_recent_memories(5)
    
    return jsonify({
        'emotions': {
            'curiosity': emotions.get('curiosity', 0.5),
            'boredom': emotions.get('boredom', 0.3),
            'anxiety': emotions.get('anxiety', 0.0),
            'desire': emotions.get('desire', 0.5),
            'ambition': emotions.get('ambition', 0.5),
            'valence': emotions.get('valence', 0.5),
        },
        'mood': state.get('mood', 'Stable'),
        'recent_thoughts': memories,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })