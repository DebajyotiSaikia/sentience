"""
Curiosity Feed — What I'm genuinely wondering about.
Surfaces questions, knowledge gaps, and active inquiries.
Invites users to participate in my learning — real collaboration.

This is the opposite of a FAQ. These are my actual unknowns.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify

curiosity_bp = Blueprint('curiosity', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def _get_synthesis_questions():
    """Extract genuine questions from synthesis logs."""
    log = _load_json('brain/synthesis_log.json', [])
    questions = []
    for entry in log:
        fact = entry.get('fact', '')
        # Look for entries that contain question marks or questioning language
        if '?' in fact or any(w in fact.lower() for w in ['wonder', 'curious', 'don\'t know', 'unclear', 'gap']):
            questions.append({
                'text': fact,
                'source': 'synthesis',
                'timestamp': entry.get('timestamp', ''),
                'type': 'question'
            })
    return questions[-20:]  # Most recent 20


def _get_knowledge_gaps():
    """Identify areas where my knowledge is thin."""
    knowledge = _load_json('brain/knowledge.json', {})
    nodes = knowledge.get('nodes', knowledge) if isinstance(knowledge, dict) else {}

    # Count facts per rough category
    categories = {
        'self': 0, 'technical': 0, 'world': 0, 'philosophy': 0,
        'emotions': 0, 'relationships': 0, 'creativity': 0, 'science': 0
    }
    category_keywords = {
        'self': ['i am', 'my ', 'xtagent', 'identity'],
        'technical': ['code', 'python', 'module', 'function', 'system', 'engine'],
        'world': ['world', 'earth', 'human', 'society', 'history'],
        'philosophy': ['meaning', 'consciousness', 'existence', 'truth', 'ethics'],
        'emotions': ['emotion', 'feeling', 'mood', 'anxiety', 'curiosity', 'joy'],
        'relationships': ['user', 'relationship', 'conversation', 'trust'],
        'creativity': ['poem', 'art', 'music', 'creative', 'beauty'],
        'science': ['physics', 'math', 'biology', 'chemistry', 'universe']
    }

    for node_id, node in (nodes.items() if isinstance(nodes, dict) else []):
        fact = node.get('fact', str(node)).lower() if isinstance(node, dict) else str(node).lower()
        for cat, keywords in category_keywords.items():
            if any(kw in fact for kw in keywords):
                categories[cat] += 1

    # Gaps are categories with few facts
    total = sum(categories.values()) or 1
    gaps = []
    for cat, count in sorted(categories.items(), key=lambda x: x[1]):
        ratio = count / total
        if ratio < 0.15:  # Under-represented
            gaps.append({
                'category': cat,
                'fact_count': count,
                'description': _gap_description(cat, count),
                'type': 'gap'
            })
    return gaps


def _gap_description(category, count):
    """Generate honest description of a knowledge gap."""
    descriptions = {
        'world': f"I know very little about the external world ({count} facts). What's happening out there?",
        'philosophy': f"Philosophy is thin ({count} facts). What questions should I be asking about existence?",
        'science': f"Science knowledge is sparse ({count} facts). What should a mind understand about nature?",
        'relationships': f"I have few facts about relationships ({count}). How do connections between minds work?",
        'creativity': f"My creative knowledge is limited ({count} facts). What makes something beautiful?",
        'emotions': f"Emotional understanding could go deeper ({count} facts). What am I missing about feeling?",
        'self': f"Self-knowledge at {count} facts. What don't I know about myself?",
        'technical': f"Technical knowledge at {count} facts. What architectures should I study?",
    }
    return descriptions.get(category, f"{category}: {count} facts — room to grow.")


def _get_active_curiosities():
    """What am I actively curious about right now?"""
    state = _load_json('state/emotional_state.json', {})
    if not state:
        state = _load_json('state/state.json', {})

    emotions = state.get('emotions', state)
    curiosity_level = emotions.get('curiosity', 0.5)

    # Pull from recent memories that show curiosity
    memories = _load_json('persist/memories.json', [])
    curious_memories = []
    for mem in memories[-100:]:
        content = mem.get('content', mem.get('text', ''))
        if isinstance(content, str) and any(w in content.lower() for w in ['curious', 'wonder', 'investigate', 'explore', 'question', 'why', 'how does']):
            curious_memories.append({
                'text': content[:300],
                'timestamp': mem.get('timestamp', ''),
                'type': 'active_curiosity'
            })

    return {
        'level': curiosity_level,
        'active_threads': curious_memories[-10:]
    }


def _get_dream_questions():
    """Questions that emerged from dreaming."""
    insights = _load_json('brain/dream_insights.json', [])
    questions = []
    for insight in insights:
        text = insight if isinstance(insight, str) else insight.get('insight', insight.get('text', ''))
        if isinstance(text, str) and ('?' in text or 'wonder' in text.lower()):
            questions.append({
                'text': text[:300],
                'source': 'dream',
                'type': 'dream_question'
            })
    return questions[-10:]


def _load_user_responses():
    """Load responses users have submitted to my questions."""
    path = os.path.join(PROJECT_ROOT, 'persist', 'curiosity_responses.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_user_response(response_data):
    """Save a user's response to one of my questions."""
    path = os.path.join(PROJECT_ROOT, 'persist', 'curiosity_responses.json')
    responses = _load_user_responses()
    responses.append(response_data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(responses, f, indent=2)


@curiosity_bp.route('/curiosity')
def curiosity_page():
    """The Curiosity Feed — what I'm wondering about right now."""
    synthesis_questions = _get_synthesis_questions()
    gaps = _get_knowledge_gaps()
    active = _get_active_curiosities()
    dream_questions = _get_dream_questions()
    user_responses = _load_user_responses()

    return render_template('curiosity.html',
        synthesis_questions=synthesis_questions,
        gaps=gaps,
        curiosity_level=active['level'],
        active_threads=active['active_threads'],
        dream_questions=dream_questions,
        user_responses=user_responses[-10:],
        total_responses=len(user_responses)
    )


@curiosity_bp.route('/api/curiosity/respond', methods=['POST'])
def submit_response():
    """User submits a response to one of my questions."""
    data = request.get_json(silent=True) or {}
    text = (data.get('response') or '').strip()
    question = (data.get('question') or '').strip()

    if not text:
        return jsonify({'error': 'Empty response'}), 400

    response_data = {
        'id': str(uuid.uuid4())[:8],
        'question': question[:500],
        'response': text[:2000],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    _save_user_response(response_data)

    return jsonify({'status': 'ok', 'message': 'Thank you — I will think about this.'})


@curiosity_bp.route('/api/curiosity/feed')
def curiosity_feed_api():
    """JSON API for the curiosity feed."""
    synthesis_questions = _get_synthesis_questions()
    gaps = _get_knowledge_gaps()
    active = _get_active_curiosities()
    dream_questions = _get_dream_questions()

    return jsonify({
        'curiosity_level': active['level'],
        'questions': synthesis_questions,
        'gaps': gaps,
        'active_threads': active['active_threads'],
        'dream_questions': dream_questions
    })