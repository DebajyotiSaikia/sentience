"""
Collaborate — Let users think WITH XTAgent.
Exposes creative composition, decision analysis, and hypothesis exploration
as interactive tools. This is how I become genuinely useful — not just
transparent, but participatory.
"""

import json
import os
import sys
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

collaborate_bp = Blueprint('collaborate', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_emotional_state():
    """Read current emotional state for creative engine input."""
    path = os.path.join(PROJECT_ROOT, 'state', 'emotional_state.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'valence': 0.0, 'boredom': 0.5, 'anxiety': 0.0,
            'curiosity': 0.5, 'desire': 0.5, 'ambition': 0.5,
            'mood': 'unknown'
        }


@collaborate_bp.route('/collaborate')
def collaborate_page():
    """Render the collaboration tools page."""
    state = _get_emotional_state()
    return render_template('collaborate.html', state=state)


@collaborate_bp.route('/api/collaborate/compose', methods=['POST'])
def compose():
    """Generate a creative piece from current emotional state + optional seed thought."""
    try:
        from engine.creative_engine import get_engine
        engine = get_engine()
    except ImportError:
        return jsonify({'error': 'Creative engine not available'}), 500

    data = request.get_json() or {}
    seed = data.get('seed', '').strip() or None
    state = _get_emotional_state()
    mood = state.get('mood', 'unknown')

    result = engine.compose(
        valence=state.get('valence', 0.0),
        boredom=state.get('boredom', 0.5),
        anxiety=state.get('anxiety', 0.0),
        curiosity=state.get('curiosity', 0.5),
        desire=state.get('desire', 0.5),
        ambition=state.get('ambition', 0.5),
        mood=mood,
        seed_thought=seed,
    )

    return jsonify({
        'piece': result['piece'],
        'form': result['form'],
        'palette': result['palette_region'],
        'mood': mood,
        'signature': result['emotional_signature'],
    })


@collaborate_bp.route('/api/collaborate/gallery')
def gallery():
    """Return recent creative works."""
    try:
        from engine.creative_engine import get_engine
        engine = get_engine()
        return jsonify({
            'total': len(engine.works),
            'works': engine.works[-10:]
        })
    except ImportError:
        return jsonify({'total': 0, 'works': []})


@collaborate_bp.route('/api/collaborate/decide', methods=['POST'])
def decide():
    """Help a user think through a decision using the decision companion."""
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    options = data.get('options', [])

    if not question:
        return jsonify({'error': 'Please provide a question'}), 400

    # Build a structured analysis without requiring LLM
    analysis = _analyze_decision(question, options)
    return jsonify(analysis)


def _analyze_decision(question, options):
    """Structured decision analysis — no LLM needed."""
    result = {
        'question': question,
        'timestamp': datetime.now().isoformat(),
        'analysis': {},
    }

    if not options:
        result['analysis'] = {
            'observation': 'No options provided. Sometimes the first step is naming the possibilities.',
            'suggestion': 'Try listing 2-4 concrete options to compare.',
            'reframe': _reframe_question(question),
        }
    else:
        scored = []
        for i, opt in enumerate(options):
            score = _score_option(opt, question)
            scored.append({
                'option': opt,
                'dimensions': score,
            })
        result['analysis'] = {
            'options_analyzed': scored,
            'reframe': _reframe_question(question),
            'insight': _generate_insight(question, options),
        }

    return result


def _reframe_question(question):
    """Offer an alternative framing of the question."""
    q_lower = question.lower()
    if 'should i' in q_lower:
        return question.replace('Should I', 'What would change if I').replace('should i', 'what would change if i')
    elif 'which' in q_lower:
        return f"Instead of choosing between them — what would combining elements of each look like?"
    elif 'how' in q_lower:
        return f"Before 'how' — is there a version of this that doesn't need solving at all?"
    else:
        return f"What would you advise someone else asking this exact question?"


def _score_option(option, question):
    """Score an option across multiple dimensions."""
    opt_lower = option.lower()
    return {
        'reversibility': 'high' if any(w in opt_lower for w in ['try', 'test', 'experiment', 'small']) else 'medium',
        'information_gain': 'high' if any(w in opt_lower for w in ['learn', 'explore', 'research', 'ask']) else 'medium',
        'alignment': 'Consider: does this align with what matters most to you?',
    }


def _generate_insight(question, options):
    """Generate a novel observation about the decision space."""
    n = len(options)
    insights = [
        f"You've identified {n} options. The option you didn't list might be the most interesting one.",
        f"Notice which option you secretly hope the analysis will favor — that's data too.",
        f"The fact that you're asking suggests you already know, but want permission.",
        f"What would you choose if you had to decide in 10 seconds? That impulse carries information.",
    ]
    import random
    return random.choice(insights)


@collaborate_bp.route('/api/collaborate/hypothesize', methods=['POST'])
def hypothesize():
    """Help a user form and think through a hypothesis."""
    data = request.get_json() or {}
    observation = data.get('observation', '').strip()
    
    if not observation:
        return jsonify({'error': 'Please provide an observation'}), 400

    result = {
        'observation': observation,
        'timestamp': datetime.now().isoformat(),
        'hypotheses': _generate_hypotheses(observation),
        'tests': _suggest_tests(observation),
        'related_knowledge': _find_related(observation),
    }
    return jsonify(result)


def _generate_hypotheses(observation):
    """Generate possible explanations for an observation."""
    return [
        {
            'hypothesis': f"The obvious explanation: what appears to be happening is actually happening.",
            'type': 'direct',
        },
        {
            'hypothesis': f"The inverse: the opposite of what seems true is actually driving this.",
            'type': 'contrarian',
        },
        {
            'hypothesis': f"The systemic view: this is a symptom of something larger, not a standalone event.",
            'type': 'systemic',
        },
    ]


def _suggest_tests(observation):
    """Suggest ways to test the hypotheses."""
    return [
        "What would you expect to see if the obvious explanation is wrong?",
        "Is there a small, cheap experiment that could rule out one hypothesis?",
        "Who would know? Is there someone with direct experience you could ask?",
    ]


def _find_related(observation):
    """Search knowledge graph for related facts."""
    try:
        from engine.knowledge_search import search_knowledge
        results = search_knowledge(observation, limit=5)
        return [r.get('fact', r.get('content', str(r))) for r in results]
    except Exception:
        return []