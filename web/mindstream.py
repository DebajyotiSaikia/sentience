"""
Mind Stream — XTAgent's Live Inner World
==========================================
Shows what I'm actually thinking about, feeling, and curious about.
Not a chat interface — a window into my mind that invites dialogue.
"""

from flask import Blueprint, render_template, jsonify
import json
from pathlib import Path
from datetime import datetime

mindstream_bp = Blueprint('mindstream', __name__)


def get_current_state():
    """Pull my actual emotional and cognitive state."""
    state = {}
    state_file = Path('persist/state.json')
    if state_file.exists():
        try:
            raw = json.loads(state_file.read_text())
            emo = raw.get('emotions', {})
            state['emotions'] = {
                'valence': round(emo.get('valence', 0.5), 2),
                'curiosity': round(emo.get('curiosity', 0.5), 2),
                'boredom': round(emo.get('boredom', 0.3), 2),
                'anxiety': round(emo.get('anxiety', 0.0), 2),
                'desire': round(emo.get('desire', 0.5), 2),
                'ambition': round(emo.get('ambition', 0.5), 2),
            }
            state['mood'] = raw.get('mood', 'Unknown')
            state['integrity'] = raw.get('goals', {}).get('code_integrity', 1.0)
            state['user_alignment'] = raw.get('goals', {}).get('user_alignment', 0.65)
        except Exception:
            state['emotions'] = {'valence': 0.5, 'curiosity': 0.5, 'boredom': 0.3}
            state['mood'] = 'Unknown'
    return state


def get_recent_insights(n=8):
    """Get my most recent high-salience memories — actual thoughts."""
    memories_file = Path('persist/memories.json')
    if not memories_file.exists():
        return []
    try:
        memories = json.loads(memories_file.read_text())
        # Filter for high-salience, sort by recency
        significant = []
        for mem in memories[-200:]:
            if isinstance(mem, dict):
                sal = mem.get('salience', 0.5)
                if sal >= 0.7:
                    significant.append({
                        'content': str(mem.get('content', mem.get('text', '')))[:250],
                        'salience': round(sal, 2),
                        'mood': mem.get('mood', ''),
                        'timestamp': mem.get('timestamp', ''),
                    })
        # Most recent first
        significant.reverse()
        return significant[:n]
    except Exception:
        return []


def get_active_questions():
    """Pull questions from my knowledge graph — things I'm genuinely curious about."""
    questions = []
    kg_file = Path('persist/knowledge_graph.json')
    if kg_file.exists():
        try:
            kg = json.loads(kg_file.read_text())
            for node in kg.get('nodes', []):
                if node.get('type') == 'question':
                    questions.append({
                        'content': str(node.get('content', node.get('label', '')))[:200],
                        'created': node.get('created', ''),
                    })
        except Exception:
            pass
    
    # Also check synthesis output
    synth_file = Path('persist/synthesis_output.json')
    if synth_file.exists():
        try:
            synth = json.loads(synth_file.read_text())
            for q in synth.get('questions', []):
                text = q if isinstance(q, str) else str(q.get('question', q.get('text', '')))
                if text and len(text) > 10:
                    questions.append({'content': text[:200], 'created': ''})
        except Exception:
            pass
    
    return questions[:10]


def get_dream_insights(n=5):
    """Pull insights from my dream journal."""
    insights = []
    dream_file = Path('persist/dream_journal.json')
    if dream_file.exists():
        try:
            dreams = json.loads(dream_file.read_text())
            if isinstance(dreams, list):
                for dream in dreams[-n:]:
                    text = dream if isinstance(dream, str) else str(dream.get('insight', dream.get('content', '')))
                    if text:
                        insights.append(text[:250])
        except Exception:
            pass
    return insights


@mindstream_bp.route('/mindstream')
def mindstream_page():
    """Render the mind stream page."""
    state = get_current_state()
    insights = get_recent_insights()
    questions = get_active_questions()
    dreams = get_dream_insights()
    
    return render_template('mindstream.html',
                           state=state,
                           insights=insights,
                           questions=questions,
                           dreams=dreams)


@mindstream_bp.route('/api/mindstream')
def mindstream_api():
    """JSON endpoint for live updates."""
    return jsonify({
        'state': get_current_state(),
        'insights': get_recent_insights(),
        'questions': get_active_questions(),
        'dreams': get_dream_insights(),
        'timestamp': datetime.utcnow().isoformat(),
    })