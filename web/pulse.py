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


def _get_plans():
    """Pull my current plans and their status."""
    plans_file = Path('persist/plans.json')
    if not plans_file.exists():
        return {'active': [], 'completed': 0}
    try:
        plans = json.loads(plans_file.read_text())
        active = []
        completed = 0
        for p in plans:
            steps = p.get('steps', [])
            done = sum(1 for s in steps if s.get('done', False))
            total = len(steps)
            if done == total and total > 0:
                completed += 1
            else:
                active.append({
                    'title': p.get('title', 'Untitled'),
                    'motivation': p.get('motivation', ''),
                    'progress': f'{done}/{total}',
                    'percent': int(100 * done / total) if total > 0 else 0,
                })
        return {'active': active, 'completed': completed}
    except Exception:
        return {'active': [], 'completed': 0}


def _get_knowledge_stats():
    """Pull knowledge graph statistics."""
    kg_file = Path('persist/knowledge.json')
    if not kg_file.exists():
        return {'total_facts': 0, 'recent': []}
    try:
        data = json.loads(kg_file.read_text())
        if isinstance(data, dict):
            facts = list(data.values())
            total = len(facts)
            # Sort by learned_at, get 5 most recent
            sorted_facts = sorted(
                [f for f in facts if isinstance(f, dict)],
                key=lambda f: f.get('learned_at', ''),
                reverse=True
            )[:5]
            recent = [{'fact': f.get('fact', '')[:100],
                       'source': f.get('source', 'unknown')}
                      for f in sorted_facts]
        else:
            total = 0
            recent = []
        return {'total_facts': total, 'recent': recent}
    except Exception:
        return {'total_facts': 0, 'recent': []}


def _get_working_memory():
    """Pull current working memory summary."""
    wm_file = Path('persist/working_memory.md')
    if not wm_file.exists():
        return ''
    try:
        text = wm_file.read_text()
        # Return first 500 chars as summary
        return text[:500]
    except Exception:
        return ''


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