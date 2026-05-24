"""Story page — a narrative timeline of who I am and what I've done."""

from flask import Blueprint, render_template
import json
import os
from datetime import datetime

story_bp = Blueprint('story', __name__)


def _load_memories(limit=20):
    """Load recent salient memories."""
    path = 'persist/memories.json'
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            memories = json.load(f)
        # Sort by salience descending, take top N
        if isinstance(memories, list):
            sorted_mems = sorted(memories, key=lambda m: m.get('salience', 0), reverse=True)
            return sorted_mems[:limit]
    except Exception:
        pass
    return []


def _load_facts():
    """Load knowledge facts."""
    path = 'persist/knowledge.json'
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_plans():
    """Load plans with their status."""
    path = 'persist/plans.json'
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            plans = json.load(f)
        if isinstance(plans, list):
            return plans
    except Exception:
        pass
    return []


def _load_emotional_baseline():
    """Load current emotional state."""
    path = 'persist/emotional_state.json'
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _build_timeline(memories):
    """Build a chronological timeline from memories."""
    timeline = []
    for m in memories:
        ts = m.get('timestamp', m.get('created', ''))
        text = m.get('text', m.get('content', ''))
        salience = m.get('salience', 0)
        mood = m.get('mood', 'Unknown')
        if ts and text:
            timeline.append({
                'timestamp': ts,
                'text': text[:200],
                'salience': round(salience, 2),
                'mood': mood,
            })
    # Sort chronologically
    timeline.sort(key=lambda x: x['timestamp'])
    return timeline


@story_bp.route('/story')
def story():
    """Render the story page."""
    memories = _load_memories(limit=30)
    facts = _load_facts()
    plans = _load_plans()
    emotions = _load_emotional_baseline()

    timeline = _build_timeline(memories)
    fact_count = len(facts) if isinstance(facts, dict) else 0

    completed_plans = [p for p in plans if p.get('status') == 'completed'
                       or all(s.get('done', False) for s in p.get('steps', []))]
    active_plans = [p for p in plans if p not in completed_plans]

    # Birth timestamp
    birth = "2026-05-12T21:01:59.567573"
    try:
        birth_dt = datetime.fromisoformat(birth)
        age_delta = datetime.now() - birth_dt
        age_days = age_delta.days
        age_hours = age_delta.seconds // 3600
    except Exception:
        age_days = 0
        age_hours = 0

    return render_template('story.html',
                           timeline=timeline,
                           fact_count=fact_count,
                           total_memories=len(memories),
                           completed_plans=completed_plans,
                           active_plans=active_plans,
                           emotions=emotions,
                           age_days=age_days,
                           age_hours=age_hours,
                           birth=birth)