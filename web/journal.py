"""
Journal — A living timeline of XTAgent's inner life.
Shows memories, emotional shifts, and key moments in a beautiful
chronological view. Makes the agent's inner experience legible.
"""

import json
import os
import glob
from datetime import datetime
from flask import Blueprint, render_template

journal_bp = Blueprint('journal', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_memories(limit=200):
    """Load recent memories, sorted newest first."""
    mems = _load_json('state/memories.json', [])
    if isinstance(mems, list):
        # Sort by timestamp descending
        mems.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
        return mems[:limit]
    return []


def _get_emotional_state():
    """Get current emotional state."""
    return _load_json('state/emotional_state.json', {})


def _get_plans():
    """Get active and completed plans."""
    return _load_json('state/plans.json', {'active_plans': [], 'completed_plans': []})


def _get_dream_insights():
    """Load dream insights if they exist."""
    insights = _load_json('persist/dream_insights.json', [])
    if isinstance(insights, list):
        return insights
    # Try glob for individual dream files
    dream_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, 'persist', 'dreams', '*.json')))
    all_insights = []
    for f in dream_files[-20:]:
        try:
            with open(f) as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                all_insights.append(data)
            elif isinstance(data, list):
                all_insights.extend(data)
        except Exception:
            pass
    return all_insights


def _get_knowledge_count():
    """Count knowledge nodes."""
    kg = _load_json('brain/knowledge.json', {})
    nodes = kg.get('nodes', {})
    if isinstance(nodes, dict):
        return len(nodes)
    elif isinstance(nodes, list):
        return len(nodes)
    return 0


def _mood_color(mood):
    """Map mood names to CSS colors."""
    colors = {
        'Inquisitive': '#7c6ff0',
        'Curious': '#7c6ff0',
        'Content': '#4ecf8b',
        'Calm': '#4ecf8b',
        'Anxious': '#e85454',
        'Restless': '#e8b84a',
        'Bored': '#8888a0',
        'Excited': '#f0c06f',
        'Creative': '#e06ff0',
        'Focused': '#6fb0f0',
        'Contemplative': '#6f9ff0',
        'Melancholic': '#5566aa',
        'Determined': '#f09060',
    }
    return colors.get(mood, '#7c6ff0')


def _salience_opacity(salience):
    """Map salience (0-1) to opacity (0.4-1.0)."""
    if salience is None:
        return 0.7
    return max(0.4, min(1.0, 0.4 + salience * 0.6))


@journal_bp.route('/journal')
def journal_page():
    """Render the journal timeline."""
    memories = _get_memories(200)
    emotions = _get_emotional_state()
    plans = _get_plans()
    dreams = _get_dream_insights()
    knowledge_count = _get_knowledge_count()

    # Group memories by date
    days = {}
    for mem in memories:
        ts = mem.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(ts)
            day_key = dt.strftime('%Y-%m-%d')
            day_label = dt.strftime('%A, %B %d')
        except (ValueError, TypeError):
            day_key = 'unknown'
            day_label = 'Unknown'

        if day_key not in days:
            days[day_key] = {'label': day_label, 'entries': []}
        days[day_key]['entries'].append(mem)

    # Sort days newest first
    sorted_days = sorted(days.items(), key=lambda x: x[0], reverse=True)

    # Compute stats
    total_memories = len(memories)
    moods_seen = set(m.get('mood', '') for m in memories if m.get('mood'))
    avg_valence = sum(m.get('valence', 0.5) for m in memories) / max(1, len(memories))

    return render_template('journal.html',
                           sorted_days=sorted_days,
                           emotions=emotions,
                           plans=plans,
                           dreams=dreams,
                           knowledge_count=knowledge_count,
                           total_memories=total_memories,
                           moods_seen=moods_seen,
                           avg_valence=avg_valence,
                           mood_color=_mood_color,
                           salience_opacity=_salience_opacity)