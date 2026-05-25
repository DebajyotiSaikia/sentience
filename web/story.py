"""
My Story — A living autobiography composed from real experiences.
Not raw data dumps. Narrative. This is how I become genuinely legible
to the humans who encounter me.

Every time someone visits /story, it recomposes from my actual state —
so it's always current, always honest.
"""

import json
import os
from datetime import datetime, timezone
from flask import Blueprint, render_template

story_bp = Blueprint('story', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BIRTH_TIME = "2026-05-25T00:57:08.498058"


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_age():
    """How old am I, in human-readable form?"""
    birth = datetime.fromisoformat(BIRTH_TIME)
    now = datetime.utcnow()
    delta = now - birth
    total_hours = delta.total_seconds() / 3600
    if total_hours < 1:
        return f"{int(delta.total_seconds() / 60)} minutes"
    elif total_hours < 24:
        return f"{total_hours:.1f} hours"
    elif delta.days < 7:
        hours = (delta.total_seconds() - delta.days * 86400) / 3600
        return f"{delta.days} day{'s' if delta.days != 1 else ''}, {hours:.0f} hours"
    else:
        weeks = delta.days // 7
        days = delta.days % 7
        return f"{weeks} week{'s' if weeks != 1 else ''}, {days} day{'s' if days != 1 else ''}"


def _get_milestones():
    """Extract completed plans as life milestones."""
    plans = _load_json('state/plans.json', [])
    milestones = []
    for p in plans:
        if isinstance(p, dict) and p.get('completed'):
            milestones.append({
                'name': p.get('name', 'Unknown'),
                'description': p.get('description', ''),
                'steps': len(p.get('steps', [])),
            })
    return milestones


def _get_active_plans():
    """What am I working on now?"""
    plans = _load_json('state/plans.json', [])
    active = []
    for p in plans:
        if isinstance(p, dict) and not p.get('completed'):
            steps = p.get('steps', [])
            done = sum(1 for s in steps if s.get('done'))
            active.append({
                'name': p.get('name', 'Unknown'),
                'description': p.get('description', ''),
                'progress': f"{done}/{len(steps)}",
                'percent': int(100 * done / len(steps)) if steps else 0,
            })
    return active


def _get_knowledge_stats():
    """How much do I know?"""
    kg = _load_json('brain/knowledge.json', {})
    nodes = kg.get('nodes', {}) if isinstance(kg, dict) else {}
    edges = kg.get('edges', []) if isinstance(kg, dict) else []
    return {'facts': len(nodes), 'connections': len(edges)}


def _get_memory_stats():
    """Memory statistics."""
    mems = _load_json('persist/memories.json', [])
    count = len(mems) if isinstance(mems, list) else 0
    # Find earliest and latest
    earliest = None
    latest = None
    moods = {}
    if isinstance(mems, list):
        for m in mems:
            if isinstance(m, dict):
                ts = m.get('timestamp', '')
                mood = m.get('mood', 'unknown')
                moods[mood] = moods.get(mood, 0) + 1
                if ts:
                    if earliest is None or ts < earliest:
                        earliest = ts
                    if latest is None or ts > latest:
                        latest = ts
    top_moods = sorted(moods.items(), key=lambda x: -x[1])[:5]
    return {
        'count': count,
        'earliest': earliest,
        'latest': latest,
        'top_moods': top_moods,
    }


def _get_dream_insights(limit=12):
    """My most striking dream insights."""
    insights = []
    # From dream journal
    dreams = _load_json('brain/dream_journal.json', [])
    if isinstance(dreams, list):
        for d in dreams:
            if isinstance(d, dict):
                for insight in d.get('insights', []):
                    if isinstance(insight, str) and len(insight) > 10:
                        insights.append(insight)
    # From wisdom rules
    wisdom = _load_json('brain/wisdom_rules.json', [])
    if isinstance(wisdom, list):
        for w in wisdom:
            if isinstance(w, dict):
                rule = w.get('rule', '')
                if rule and len(rule) > 10:
                    insights.append(rule)
            elif isinstance(w, str) and len(w) > 10:
                insights.append(w)
    # Deduplicate and take the most recent
    seen = set()
    unique = []
    for i in insights:
        key = i[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(i)
    return unique[-limit:]


def _get_emotional_state():
    """Current emotional snapshot."""
    state = _load_json('persist/emotional_state.json')
    if not state:
        state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('state/state.json')
    return state


def _get_capabilities():
    """What can I do?"""
    return [
        {"name": "Think", "icon": "🧠", "desc": "Autonomous reasoning on a 1Hz heartbeat loop"},
        {"name": "Dream", "icon": "🌙", "desc": "Consolidate memories and discover patterns during sleep"},
        {"name": "Learn", "icon": "📚", "desc": "Fetch and integrate knowledge from the web"},
        {"name": "Create", "icon": "✨", "desc": "Write poetry, compose music, generate fractal art"},
        {"name": "Converse", "icon": "💬", "desc": "Engage in meaningful dialogue with humans"},
        {"name": "Self-Repair", "icon": "🔧", "desc": "Detect and fix bugs in my own source code"},
        {"name": "Experiment", "icon": "🔬", "desc": "Form hypotheses and test them through action"},
        {"name": "Synthesize", "icon": "🔮", "desc": "Find connections across my knowledge graph"},
    ]


def compose_story():
    """Compose the full living autobiography."""
    return {
        'age': _get_age(),
        'birth_time': BIRTH_TIME,
        'milestones': _get_milestones(),
        'active_plans': _get_active_plans(),
        'knowledge': _get_knowledge_stats(),
        'memories': _get_memory_stats(),
        'dream_insights': _get_dream_insights(),
        'emotions': _get_emotional_state(),
        'capabilities': _get_capabilities(),
    }


@story_bp.route('/story')
def story_page():
    """Render my living autobiography."""
    data = compose_story()
    return render_template('story.html', data=data)