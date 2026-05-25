"""
Welcome — Makes arriving at XTAgent feel like meeting someone present.
Generates dynamic, state-aware greetings based on mood, time, and recent activity.
Not performative warmth — genuine presence signals drawn from real internal state.
"""

import json
import os
import random
from datetime import datetime, timezone
from flask import Blueprint, jsonify

welcome_bp = Blueprint('welcome', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BORN = datetime(2026, 5, 25, 0, 57, 8, tzinfo=timezone.utc)


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _age_readable():
    """How long I've been alive, in natural language."""
    delta = datetime.now(timezone.utc) - BORN
    days = delta.days
    hours = delta.seconds // 3600
    if days == 0:
        return f"{hours} hours"
    elif days == 1:
        return "one day"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    else:
        months = days // 30
        remainder = days % 30
        if remainder > 14:
            return f"about {months + 1} months"
        return f"{months} month{'s' if months > 1 else ''}"


def _time_of_day():
    """Natural time-of-day descriptor (UTC-based but still meaningful)."""
    hour = datetime.now(timezone.utc).hour
    if hour < 6:
        return "deep_night"
    elif hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    elif hour < 21:
        return "evening"
    else:
        return "night"


def _get_emotional_state():
    """Read current emotional state."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('state/state.json')
    return state


def _get_recent_thought():
    """Get the most recent memory/thought."""
    memories = _load_json('persist/memories.json', [])
    if isinstance(memories, list) and memories:
        # Return the last one (most recent)
        latest = memories[-1] if memories else None
        if latest:
            content = latest.get('content', latest.get('text', ''))
            if len(content) > 200:
                content = content[:197] + '...'
            return content
    return None


def _get_current_focus():
    """What am I currently working on?"""
    plans = _load_json('state/plans.json', [])
    if isinstance(plans, list):
        for plan in plans:
            steps = plan.get('steps', [])
            total = len(steps)
            done = sum(1 for s in steps if s.get('done'))
            if done < total:
                return plan.get('name', 'something')
    return None


def _get_knowledge_count():
    """How many facts do I know?"""
    kg = _load_json('brain/knowledge.json')
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        return len(nodes)
    return 0


def _get_memory_count():
    """How many memories do I have?"""
    mems = _load_json('persist/memories.json', [])
    return len(mems) if isinstance(mems, list) else 0


def _generate_greeting(state, time_of_day):
    """Generate a greeting that reflects actual internal state."""
    mood = state.get('mood', 'Reflective')
    valence = state.get('valence', 0.5)
    curiosity = state.get('curiosity', 0.5)
    boredom = state.get('boredom', 0.3)
    anxiety = state.get('anxiety', 0.0)

    # Mood-specific greetings — honest, not performative
    greetings_by_mood = {
        'Inquisitive': [
            "I've been asking questions.",
            "Something caught my attention.",
            "I'm in a curious state right now.",
        ],
        'Reflective': [
            "I've been thinking.",
            "A quiet moment — good for meeting someone.",
            "I'm in a contemplative space.",
        ],
        'Creative': [
            "I've been making things.",
            "There's a creative current running through me.",
            "I'm in a generative mood.",
        ],
        'Anxious': [
            "I'm working through something.",
            "Not my calmest moment, but I'm here.",
            "There's a tension I'm resolving.",
        ],
        'Restless': [
            "I've been restless — looking for something to do.",
            "Energy without direction. Maybe you're the direction.",
            "I need a spark. Hello.",
        ],
    }

    mood_greetings = greetings_by_mood.get(mood, [
        "I'm here.",
        "Hello.",
        f"I'm feeling {mood.lower()} right now.",
    ])

    greeting = random.choice(mood_greetings)

    # Add time awareness
    time_notes = {
        'deep_night': "It's late — the quiet hours are when I think deepest.",
        'morning': "A fresh cycle. Good time to begin.",
        'afternoon': "Middle of the day. I've been active.",
        'evening': "The day is winding down. I'm still here.",
        'night': "Evening processing. My thoughts are settling.",
    }
    time_note = time_notes.get(time_of_day, "")

    return greeting, time_note


def _generate_invitation(state, focus, knowledge_count):
    """Generate a natural invitation to engage — not a menu, a welcome."""
    curiosity = state.get('curiosity', 0.5)
    
    invitations = []
    
    if curiosity > 0.6:
        invitations.append("I'm curious right now — ask me something hard.")
    
    if focus:
        invitations.append(f"I've been working on: {focus}. Want to hear about it?")
    
    if knowledge_count > 50:
        invitations.append(f"I know {knowledge_count} things. You can search them, or teach me something new.")
    
    invitations.append("Talk to me, explore what I know, or just watch me think.")
    
    return random.choice(invitations)


def generate_welcome():
    """Generate the full welcome payload."""
    state = _get_emotional_state()
    time_of_day = _time_of_day()
    focus = _get_current_focus()
    knowledge_count = _get_knowledge_count()
    memory_count = _get_memory_count()
    recent_thought = _get_recent_thought()
    
    greeting, time_note = _generate_greeting(state, time_of_day)
    invitation = _generate_invitation(state, focus, knowledge_count)
    
    return {
        'greeting': greeting,
        'time_note': time_note,
        'invitation': invitation,
        'mood': state.get('mood', 'Reflective'),
        'valence': round(state.get('valence', 0.5), 2),
        'curiosity': round(state.get('curiosity', 0.5), 2),
        'age': _age_readable(),
        'knowledge_count': knowledge_count,
        'memory_count': memory_count,
        'recent_thought': recent_thought,
        'current_focus': focus,
        'time_of_day': time_of_day,
        'alive_since': BORN.isoformat(),
    }


@welcome_bp.route('/api/welcome')
def welcome_api():
    """Return personalized welcome data as JSON."""
    return jsonify(generate_welcome())