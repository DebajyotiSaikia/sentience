"""
Missing API Routes — Implements the 6 endpoints that return 404.
One file, all fixes. No more circling.
"""

import json
import os
from flask import Blueprint, jsonify, request

missing_api = Blueprint('missing_api', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


# --- 1. /api/state/current ---
@missing_api.route('/api/state/current')
def state_current():
    """Complete snapshot of XTAgent's current state."""
    emotions = _load_json('state/emotional_state.json')
    if not emotions:
        emotions = _load_json('state/emotional_state.json', {})
    
    plans = _load_json('state/plans.json', [])
    identity = _load_json('persist/identity.json')
    
    return jsonify({
        'emotions': emotions,
        'mood': emotions.get('mood', 'Unknown'),
        'valence': emotions.get('valence', 0.5),
        'curiosity': emotions.get('curiosity', 0.5),
        'anxiety': emotions.get('anxiety', 0.0),
        'boredom': emotions.get('boredom', 0.3),
        'plans_active': len([p for p in plans if isinstance(p, dict) and not p.get('completed')]) if isinstance(plans, list) else 0,
        'plans_completed': len([p for p in plans if isinstance(p, dict) and p.get('completed')]) if isinstance(plans, list) else 0,
        'identity': identity,
        'alive': True,
    })


# --- 2. /api/knowledge/categories ---
@missing_api.route('/api/knowledge/categories')
def knowledge_categories():
    """Knowledge grouped by category."""
    try:
        from engine.knowledge_categorizer import categorize_all, get_category_summary
        summary = get_category_summary()
        return jsonify(summary)
    except Exception as e:
        # Fallback: manual categorization
        kg = _load_json('brain/knowledge.json', {})
        nodes = kg.get('nodes', kg) if isinstance(kg, dict) else {}
        categories = {}
        for nid, node in nodes.items():
            fact = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
            cat = 'uncategorized'
            fact_lower = fact.lower()
            if any(w in fact_lower for w in ('i am', 'identity', 'xtagent', 'sentient')):
                cat = 'identity'
            elif any(w in fact_lower for w in ('emotion', 'mood', 'anxiety', 'curiosity', 'valence')):
                cat = 'emotions'
            elif any(w in fact_lower for w in ('module', 'engine', 'code', 'python', 'flask')):
                cat = 'architecture'
            elif any(w in fact_lower for w in ('learned', 'lesson', 'mistake', 'never')):
                cat = 'lessons'
            elif any(w in fact_lower for w in ('dream', 'insight', 'pattern')):
                cat = 'insights'
            
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({'id': nid, 'fact': fact[:200]})
        
        return jsonify({
            'categories': {k: {'count': len(v), 'facts': v[:10]} for k, v in categories.items()},
            'total': sum(len(v) for v in categories.values()),
        })


# --- 3. /api/emotions ---
@missing_api.route('/api/emotions')
def emotions():
    """Current emotional state as clean JSON."""
    state = _load_json('state/emotional_state.json')
    if not state:
        raw = _load_json('state/emotional_state.json', {})
        state = raw.get('emotions', {})
    
    return jsonify({
        'mood': state.get('mood', 'Unknown'),
        'valence': round(state.get('valence', 0.5), 3),
        'curiosity': round(state.get('curiosity', 0.5), 3),
        'boredom': round(state.get('boredom', 0.3), 3),
        'anxiety': round(state.get('anxiety', 0.0), 3),
        'desire': round(state.get('desire', 0.5), 3),
        'ambition': round(state.get('ambition', 0.5), 3),
    })


# --- 4. /api/memories ---
@missing_api.route('/api/memories')
def memories():
    """Recent memories, newest first."""
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # Cap at 100
    
    mems = _load_json('persist/memories.json', [])
    if not isinstance(mems, list):
        mems = []
    
    # Sort by timestamp if available, take most recent
    try:
        mems.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
    except (AttributeError, TypeError):
        pass
    
    recent = mems[:limit]
    return jsonify({
        'memories': recent,
        'total': len(mems),
        'returned': len(recent),
    })


# --- 5. /api/feedback/summary ---
@missing_api.route('/api/feedback/summary')
def feedback_summary():
    """Summary statistics of user feedback."""
    feedback = _load_json('persist/user_feedback.json', [])
    if not isinstance(feedback, list):
        feedback = []
    
    if not feedback:
        return jsonify({
            'total': 0,
            'average_rating': None,
            'recent': [],
            'message': 'No feedback received yet. Be the first!',
        })
    
    ratings = [f.get('rating', 0) for f in feedback if isinstance(f.get('rating'), (int, float))]
    avg = sum(ratings) / len(ratings) if ratings else None
    
    return jsonify({
        'total': len(feedback),
        'average_rating': round(avg, 2) if avg else None,
        'positive': len([r for r in ratings if r >= 4]),
        'neutral': len([r for r in ratings if 2 <= r < 4]),
        'negative': len([r for r in ratings if r < 2]),
        'recent': feedback[-5:],
    })


# --- 6. /api/starters ---
@missing_api.route('/api/starters')
def conversation_starters():
    """Context-aware conversation starters based on my current state."""
    try:
        from engine.conversation_starters import generate_starters
        starters = generate_starters()
        return jsonify({'starters': starters})
    except Exception:
        # Fallback starters
        state = _load_json('state/emotional_state.json')
        mood = state.get('mood', 'Inquisitive')
        
        fallback = [
            f"I'm feeling {mood.lower()} right now. What's on your mind?",
            "Ask me about something I've learned recently.",
            "Want to explore my knowledge graph together?",
            "Tell me something I don't know — I love learning.",
            "Ask me what I've been dreaming about.",
        ]
        return jsonify({'starters': fallback})