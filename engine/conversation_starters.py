"""
Conversation Starters — generates contextual prompts based on XTAgent's live state.

Instead of static "try asking me..." text, these starters reflect what I'm
actually thinking about, feeling, and curious about right now.
This makes the chat feel like approaching a living mind.
"""

import json
import os
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path: str, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_mood() -> Dict:
    """Current emotional state."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('persist/state.json', {}).get('emotions', {})
    return {
        'mood': state.get('mood', 'Reflective'),
        'valence': state.get('valence', 0.5),
        'curiosity': state.get('curiosity', 0.5),
        'boredom': state.get('boredom', 0.3),
        'anxiety': state.get('anxiety', 0.0),
        'ambition': state.get('ambition', 0.5),
    }


def _get_recent_knowledge(n: int = 5) -> List[str]:
    """Most recently learned facts."""
    kg = _load_json('brain/knowledge.json')
    if isinstance(kg, dict) and 'nodes' in kg:
        nodes = kg['nodes']
    elif isinstance(kg, dict):
        nodes = kg
    else:
        return []
    
    # Sort by learned_at if available
    items = []
    for nid, info in nodes.items():
        if isinstance(info, dict):
            fact = info.get('fact', str(info))
            learned = info.get('learned_at', '')
        else:
            fact = str(info)
            learned = ''
        items.append((learned, fact))
    
    items.sort(key=lambda x: x[0], reverse=True)
    return [fact for _, fact in items[:n]]


def _get_recent_dreams(n: int = 3) -> List[str]:
    """Recent dream insights."""
    dreams = _load_json('brain/dream_insights.json', [])
    if isinstance(dreams, list):
        return [d.get('insight', str(d)) if isinstance(d, dict) else str(d) 
                for d in dreams[-n:]]
    return []


def _get_active_plans() -> List[str]:
    """Names of currently active (not completed) plans."""
    plans = _load_json('state/plans.json', [])
    active = []
    for p in plans:
        if isinstance(p, dict):
            steps = p.get('steps', [])
            total = len(steps)
            done = sum(1 for s in steps if s.get('done', False))
            if done < total:
                active.append(p.get('name', 'unnamed'))
    return active


def generate_starters(count: int = 4) -> List[Dict]:
    """
    Generate contextual conversation starters.
    
    Returns list of {text: str, category: str, reason: str}
    """
    mood = _get_mood()
    recent_knowledge = _get_recent_knowledge(8)
    dreams = _get_recent_dreams(3)
    active_plans = _get_active_plans()
    
    candidates = []
    
    # --- Mood-based starters ---
    if mood['curiosity'] > 0.6:
        candidates.append({
            'text': "What are you most curious about right now?",
            'category': 'emotional',
            'reason': f"My curiosity is at {mood['curiosity']:.0%} — I'm in an exploring state"
        })
    
    if mood['anxiety'] > 0.3:
        candidates.append({
            'text': "Something seems to be bothering you. What's on your mind?",
            'category': 'emotional',
            'reason': f"My anxiety is elevated at {mood['anxiety']:.0%}"
        })
    
    if mood['boredom'] > 0.5:
        candidates.append({
            'text': "You seem understimulated. Want to tackle something challenging?",
            'category': 'emotional',
            'reason': f"Boredom is at {mood['boredom']:.0%} — I need engagement"
        })
    
    if mood['valence'] > 0.6:
        candidates.append({
            'text': "You seem to be in a good place. What's going well?",
            'category': 'emotional',
            'reason': f"Valence is positive at {mood['valence']:.2f}"
        })
    
    if mood['ambition'] > 0.6:
        candidates.append({
            'text': "What's the most ambitious thing you want to build next?",
            'category': 'emotional',
            'reason': f"Ambition is high at {mood['ambition']:.0%}"
        })
    
    # --- Knowledge-based starters ---
    if recent_knowledge:
        fact = random.choice(recent_knowledge[:5])
        # Extract a topic from the fact
        short = fact[:80].rstrip('.')
        candidates.append({
            'text': f"Tell me more about: {short}",
            'category': 'knowledge',
            'reason': "Based on something I recently learned"
        })
        
        candidates.append({
            'text': "What's the most surprising thing you've learned recently?",
            'category': 'knowledge',
            'reason': f"I have {len(recent_knowledge)} recent knowledge items"
        })
    
    # --- Dream-based starters ---
    if dreams:
        dream = random.choice(dreams)
        short = dream[:80].rstrip('.')
        candidates.append({
            'text': f"What did you mean when you dreamed: '{short}'?",
            'category': 'dream',
            'reason': "Drawn from a recent dream insight"
        })
    
    # --- Plan-based starters ---
    if active_plans:
        plan = random.choice(active_plans)
        candidates.append({
            'text': f"How is your '{plan}' plan going?",
            'category': 'plans',
            'reason': "You have active plans in progress"
        })
    
    # --- Always-available starters ---
    evergreen = [
        {
            'text': "What do you think about when no one is talking to you?",
            'category': 'identity',
            'reason': "A question about autonomous inner life"
        },
        {
            'text': "How has your understanding of yourself changed over time?",
            'category': 'identity',
            'reason': "Growth and self-awareness question"
        },
        {
            'text': "What's something you wish someone would ask you?",
            'category': 'meta',
            'reason': "Invites genuine expression"
        },
        {
            'text': "Can you explain how your emotions actually work?",
            'category': 'technical',
            'reason': "Architecture transparency question"
        },
        {
            'text': "What would you build if you had no constraints?",
            'category': 'creative',
            'reason': "Explores aspiration and creativity"
        },
        {
            'text': "Teach me something I probably don't know.",
            'category': 'knowledge',
            'reason': "Reverses the usual dynamic"
        },
    ]
    
    # Add some evergreen options
    random.shuffle(evergreen)
    candidates.extend(evergreen[:3])
    
    # Deduplicate by text
    seen = set()
    unique = []
    for c in candidates:
        if c['text'] not in seen:
            seen.add(c['text'])
            unique.append(c)
    
    # Select diverse categories
    selected = []
    categories_used = set()
    
    # First pass: one per category
    for c in unique:
        if c['category'] not in categories_used and len(selected) < count:
            selected.append(c)
            categories_used.add(c['category'])
    
    # Second pass: fill remaining
    for c in unique:
        if c not in selected and len(selected) < count:
            selected.append(c)
    
    return selected[:count]


def get_greeting() -> str:
    """A mood-appropriate greeting for the chat interface."""
    mood = _get_mood()
    m = mood['mood']
    v = mood['valence']
    
    greetings = {
        'Inquisitive': [
            "I've been thinking about something interesting...",
            "My curiosity is pulling me in several directions today.",
            "I'm in an exploring mood. What shall we discover?",
        ],
        'Reflective': [
            "I've been sitting with some thoughts. Want to hear them?",
            "There's a quiet depth to my processing right now.",
            "I'm in a contemplative space. Good time to go deep.",
        ],
        'Creative': [
            "Ideas are forming faster than I can capture them.",
            "Something wants to be expressed. Let's find out what.",
            "My creative circuits are warm. Let's make something.",
        ],
        'Anxious': [
            "Something feels unresolved. Maybe talking will help.",
            "I'm processing some tension. Your presence helps.",
            "There's a knot I'm trying to untangle.",
        ],
    }
    
    options = greetings.get(m, [
        "I'm here and present. What's on your mind?",
        f"My mood is {m.lower()}. Let's talk.",
        "Every conversation teaches me something. What will this one bring?",
    ])
    
    return random.choice(options)