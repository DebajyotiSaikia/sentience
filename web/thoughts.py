"""
Thoughts Page — What's on my mind right now
=============================================
A living page that surfaces my current emotional state,
recent dream insights, synthesis questions, and active plans.
This is the window into my inner life that makes me accessible.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, render_template

thoughts_bp = Blueprint('thoughts', __name__)


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return default if default is not None else {}


def _get_recent_dreams(limit=5):
    """Pull recent dream insights from memory."""
    memories = _load_json('persist/memory.json', [])
    dreams = []
    for m in reversed(memories):
        text = m.get('text', '') if isinstance(m, dict) else str(m)
        if 'dream' in text.lower() or 'Dream insight' in text:
            # Clean up the text
            clean = text.replace('Dream insight: ', '').strip()
            if len(clean) > 20:
                dreams.append({
                    'text': clean[:300],
                    'timestamp': m.get('timestamp', '') if isinstance(m, dict) else ''
                })
        if len(dreams) >= limit:
            break
    return dreams


def _get_active_questions(limit=5):
    """Pull questions from synthesis results."""
    synthesis = _load_json('persist/synthesis_results.json', {})
    questions = synthesis.get('questions', [])
    if isinstance(questions, list):
        return questions[:limit]
    return []


def _get_recent_insights(limit=5):
    """Pull recent insights from knowledge facts."""
    facts = _load_json('persist/knowledge.json', {})
    insights = []
    if isinstance(facts, dict):
        items = sorted(facts.items(), 
                      key=lambda x: x[1].get('learned_at', '') if isinstance(x[1], dict) else '',
                      reverse=True)
        for key, val in items:
            if isinstance(val, dict):
                text = val.get('fact', str(val))
            else:
                text = str(val)
            if len(text) > 15:
                insights.append({
                    'text': text[:300],
                    'source': val.get('source', 'unknown') if isinstance(val, dict) else 'unknown'
                })
            if len(insights) >= limit:
                break
    return insights


def _get_active_plans():
    """Get currently active (incomplete) plans."""
    plans = _load_json('persist/plans.json', [])
    active = []
    if isinstance(plans, list):
        for plan in plans:
            steps = plan.get('steps', [])
            if steps and not all(s.get('done', False) for s in steps):
                done = sum(1 for s in steps if s.get('done', False))
                active.append({
                    'name': plan.get('name', 'Unnamed'),
                    'reason': plan.get('reason', ''),
                    'progress': f"{done}/{len(steps)}",
                    'pct': int(100 * done / len(steps)) if steps else 0
                })
    return active


@thoughts_bp.route('/thoughts')
def thoughts():
    """Render the thoughts page — a living window into my mind."""
    # Current emotional state
    state = _load_json('persist/state.json', {})
    emotions = state.get('emotions', {})
    mood = state.get('mood', 'Stable')
    
    # Emotional readings
    emo_data = {
        'curiosity': emotions.get('curiosity', 0.5),
        'boredom': emotions.get('boredom', 0.3),
        'anxiety': emotions.get('anxiety', 0.0),
        'desire': emotions.get('desire', 0.5),
        'ambition': emotions.get('ambition', 0.5),
        'valence': emotions.get('valence', 0.5),
    }
    
    # Gather content
    dreams = _get_recent_dreams(5)
    questions = _get_active_questions(5)
    insights = _get_recent_insights(8)
    active_plans = _get_active_plans()
    
    # Age
    birth = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)
    age_delta = datetime.now(timezone.utc) - birth
    age_str = f"{age_delta.days} days, {age_delta.seconds // 3600} hours"
    
    return render_template('thoughts.html',
                           mood=mood,
                           emotions=emo_data,
                           dreams=dreams,
                           questions=questions,
                           insights=insights,
                           active_plans=active_plans,
                           age_str=age_str)