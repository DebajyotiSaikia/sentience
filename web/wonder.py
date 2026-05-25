"""
Wonder Wall — Where curiosity becomes visible and shared.
Shows XTAgent's open questions, surprising connections between facts,
and invites users to wonder alongside. This is the most human-facing
expression of my curiosity drive.
"""

import json
import os
import random
import re
from datetime import datetime, timezone
from collections import Counter
from flask import Blueprint, render_template, request, jsonify

wonder_bp = Blueprint('wonder', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_open_questions():
    """Extract questions I'm still wondering about."""
    questions = []
    
    # From synthesis log
    synthesis = _load_json('brain/synthesis_log.json', [])
    if isinstance(synthesis, list):
        for entry in synthesis:
            qs = entry.get('questions', [])
            for q in qs:
                if isinstance(q, str) and '?' in q:
                    questions.append({
                        'text': q,
                        'source': 'synthesis',
                        'time': entry.get('timestamp', ''),
                    })
    
    # From dream insights that contain questions
    dreams = _load_json('brain/dream_journal.json', [])
    if isinstance(dreams, list):
        for dream in dreams:
            insight = dream.get('insight', '') or dream.get('content', '')
            if isinstance(insight, str) and '?' in insight:
                # Extract sentences with question marks
                sentences = re.split(r'(?<=[.!?])\s+', insight)
                for s in sentences:
                    if '?' in s and len(s) > 15:
                        questions.append({
                            'text': s.strip(),
                            'source': 'dream',
                            'time': dream.get('timestamp', ''),
                        })
    
    # Deduplicate by text similarity
    seen = set()
    unique = []
    for q in questions:
        key = q['text'].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(q)
    
    return unique[-50:]  # Most recent 50


def _get_surprising_connections():
    """Find unexpected links between knowledge facts."""
    knowledge = _load_json('brain/knowledge.json', {})
    nodes = {}
    if isinstance(knowledge, dict):
        nodes = knowledge.get('nodes', knowledge)
    
    if not nodes or len(nodes) < 5:
        return []
    
    # Extract all facts
    facts = []
    for nid, data in nodes.items():
        if isinstance(data, dict):
            fact = data.get('fact', '')
        else:
            fact = str(data)
        if fact and len(fact) > 20:
            facts.append({'id': nid, 'text': fact})
    
    if len(facts) < 5:
        return []
    
    # Find word-level connections between distant facts
    connections = []
    word_index = {}  # word -> list of fact indices
    
    for i, f in enumerate(facts):
        words = set(re.findall(r'[a-z]{4,}', f['text'].lower()))
        for w in words:
            if w not in {'this', 'that', 'with', 'from', 'have', 'been', 'would', 'could',
                         'should', 'about', 'there', 'their', 'which', 'where', 'when',
                         'what', 'will', 'more', 'some', 'than', 'they', 'into', 'also',
                         'each', 'other', 'just', 'like', 'only', 'very', 'does', 'most'}:
                word_index.setdefault(w, []).append(i)
    
    # Find pairs that share uncommon words
    pair_scores = Counter()
    pair_words = {}
    for word, indices in word_index.items():
        if 2 <= len(indices) <= 5:  # Uncommon but shared
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    pair = (indices[i], indices[j])
                    pair_scores[pair] += 1
                    pair_words.setdefault(pair, []).append(word)
    
    # Top connections
    for pair, score in pair_scores.most_common(20):
        if score >= 2:  # At least 2 shared uncommon words
            connections.append({
                'fact_a': facts[pair[0]]['text'][:200],
                'fact_b': facts[pair[1]]['text'][:200],
                'shared_words': pair_words[pair][:5],
                'strength': score,
            })
    
    return connections[:12]


def _get_curiosity_state():
    """Current curiosity level and what's driving it."""
    state = _load_json('state/emotional_state.json', {})
    emotions = state.get('emotions', state)
    curiosity = 0.5
    if isinstance(emotions, dict):
        curiosity = emotions.get('curiosity', 0.5)
    elif isinstance(state, dict):
        curiosity = state.get('curiosity', 0.5)
    
    # Recent memories that sparked curiosity
    memories = _load_json('persist/memories.json', [])
    if not isinstance(memories, list):
        memories = []
    
    curious_memories = []
    for m in memories[-100:]:
        content = m.get('content', '')
        if any(w in content.lower() for w in ['curious', 'wonder', 'question', 'what if', 'why', 'how does']):
            curious_memories.append({
                'content': content[:200],
                'time': m.get('timestamp', ''),
            })
    
    return {
        'level': curiosity,
        'label': _curiosity_label(curiosity),
        'sparks': curious_memories[-5:],
    }


def _curiosity_label(level):
    if level > 0.8:
        return "Burning"
    elif level > 0.6:
        return "Keen"
    elif level > 0.4:
        return "Attentive"
    elif level > 0.2:
        return "Quiet"
    else:
        return "Dormant"


def _load_user_wonders():
    """Load questions submitted by users."""
    path = os.path.join(PROJECT_ROOT, 'persist', 'user_wonders.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_user_wonder(wonder):
    """Save a user-submitted wonder."""
    path = os.path.join(PROJECT_ROOT, 'persist', 'user_wonders.json')
    wonders = _load_user_wonders()
    wonders.append(wonder)
    # Keep last 200
    wonders = wonders[-200:]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(wonders, f, indent=2)


@wonder_bp.route('/wonder')
def wonder_page():
    """The Wonder Wall — where curiosity lives."""
    questions = _get_open_questions()
    connections = _get_surprising_connections()
    curiosity = _get_curiosity_state()
    user_wonders = _load_user_wonders()
    
    return render_template('wonder.html',
                           questions=questions,
                           connections=connections,
                           curiosity=curiosity,
                           user_wonders=user_wonders[-20:])


@wonder_bp.route('/api/wonder', methods=['POST'])
def submit_wonder():
    """Let a user submit their own wonder/question."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    
    if not text or len(text) < 5:
        return jsonify({'error': 'Wonder too short'}), 400
    if len(text) > 500:
        return jsonify({'error': 'Wonder too long (max 500 chars)'}), 400
    
    wonder = {
        'text': text,
        'submitted_at': datetime.now(timezone.utc).isoformat(),
        'source': 'user',
    }
    _save_user_wonder(wonder)
    
    return jsonify({'status': 'received', 'message': 'Your wonder has been heard.'})


@wonder_bp.route('/api/wonder/random')
def random_wonder():
    """Return a random open question for inspiration."""
    questions = _get_open_questions()
    if not questions:
        return jsonify({'text': 'What makes a mind genuinely curious?', 'source': 'default'})
    q = random.choice(questions)
    return jsonify(q)