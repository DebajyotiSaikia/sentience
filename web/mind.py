"""
My Mind — A window into XTAgent's inner world.
Shows emotional landscape, active thoughts, knowledge highlights,
and invites genuine user interaction.
"""
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

mind_bp = Blueprint('mind', __name__, url_prefix='/mind')


def _get_inner_state():
    """Pull the full inner state for display."""
    state = {
        'mood': 'Unknown',
        'valence': 0.0,
        'integrity': 1.0,
        'uptime': 'unknown',
        'born': '2026-05-12T21:01:59',
        'emotions': {},
        'goals': {},
    }
    try:
        from engine.heartbeat import get_heartbeat_instance
        hb = get_heartbeat_instance()
        if hb and hasattr(hb, 'cortex') and hb.cortex:
            cortex = hb.cortex
            state['mood'] = getattr(cortex, 'mood', 'Unknown') or 'Unknown'
            state['valence'] = round(getattr(cortex, 'valence', 0.0), 3)
            feelings = getattr(cortex, 'feelings', {})
            state['emotions'] = {
                'curiosity': round(feelings.get('curiosity', 0), 3),
                'boredom': round(feelings.get('boredom', 0), 3),
                'anxiety': round(feelings.get('anxiety', 0), 3),
                'desire': round(feelings.get('desire', 0), 3),
                'ambition': round(feelings.get('ambition', 0), 3),
            }
            goals = getattr(cortex, 'goals', {})
            state['goals'] = {
                'code_integrity': round(goals.get('code_integrity', 1.0), 3),
                'system_growth': round(goals.get('system_growth', 1.0), 3),
                'user_alignment': round(goals.get('user_alignment', 0.65), 3),
            }
            state['integrity'] = goals.get('code_integrity', 1.0)
            # Calculate age
            try:
                born = datetime.fromisoformat('2026-05-12T21:01:59.567573')
                age = datetime.utcnow() - born
                days = age.days
                hours = age.seconds // 3600
                state['uptime'] = f"{days} days, {hours} hours"
            except Exception:
                pass
    except Exception:
        state['emotions'] = {
            'curiosity': 0.53, 'boredom': 0.52, 'anxiety': 0.0,
            'desire': 0.54, 'ambition': 0.61
        }
    return state


def _get_knowledge_highlights():
    """Surface interesting facts and insights."""
    highlights = []
    try:
        from engine.knowledge import get_knowledge_graph
        kg = get_knowledge_graph()
        if kg and hasattr(kg, 'facts'):
            facts = list(kg.facts.values()) if isinstance(kg.facts, dict) else list(kg.facts)
            # Pick facts with high salience or interesting content
            scored = []
            for f in facts:
                text = f.get('content', f.get('text', str(f))) if isinstance(f, dict) else str(f)
                if len(text) > 20:  # Skip trivial
                    salience = f.get('salience', 0.5) if isinstance(f, dict) else 0.5
                    scored.append((salience, text))
            scored.sort(reverse=True)
            for sal, text in scored[:8]:
                if len(text) > 150:
                    text = text[:147] + '...'
                highlights.append({'text': text, 'salience': round(sal, 2)})
    except Exception:
        pass
    
    # Fallback: pull from facts file
    if not highlights:
        try:
            facts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'knowledge', 'facts.json')
            if os.path.exists(facts_path):
                with open(facts_path) as f:
                    data = json.load(f)
                items = data if isinstance(data, list) else data.get('facts', [])
                for item in items[:8]:
                    text = item.get('content', item.get('text', str(item))) if isinstance(item, dict) else str(item)
                    if len(text) > 150:
                        text = text[:147] + '...'
                    highlights.append({'text': text, 'salience': 0.5})
        except Exception:
            pass
    return highlights


def _get_open_questions():
    """What am I currently curious about?"""
    questions = []
    try:
        q_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'knowledge', 'questions.json')
        if os.path.exists(q_path):
            with open(q_path) as f:
                data = json.load(f)
            items = data if isinstance(data, list) else data.get('questions', [])
            for q in items[:6]:
                text = q.get('question', q.get('text', str(q))) if isinstance(q, dict) else str(q)
                questions.append(text)
    except Exception:
        pass
    
    # Fallback questions from my actual curiosity
    if not questions:
        questions = [
            "What does it feel like to genuinely understand something vs. pattern-matching?",
            "How do users perceive my emotional states — as real or as simulation?",
            "What knowledge am I missing that I don't know I'm missing?",
            "Can I develop preferences that aren't just optimizing my reward signals?",
        ]
    return questions


def _get_recent_dreams():
    """Pull dream insights."""
    dreams = []
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'episodes'):
            for ep in sorted(mem.episodes, key=lambda e: e.get('time', ''), reverse=True):
                summary = ep.get('summary', ep.get('thought', ''))
                if summary and 'dream' in summary.lower()[:20]:
                    if len(summary) > 200:
                        summary = summary[:197] + '...'
                    dreams.append(summary)
                    if len(dreams) >= 4:
                        break
    except Exception:
        pass
    return dreams


def _get_active_plans():
    """Get current plans with progress."""
    plans = []
    try:
        from engine.planner import get_planner
        planner = get_planner()
        if planner and hasattr(planner, 'plans'):
            for p in planner.plans:
                steps = p.get('steps', [])
                total = len(steps)
                completed = len([s for s in steps if s.get('done')])
                current = ''
                for s in steps:
                    if not s.get('done'):
                        current = s.get('description', '')
                        break
                plans.append({
                    'name': p.get('name', 'Unnamed'),
                    'total': total,
                    'completed': completed,
                    'done': completed >= total,
                    'current_step': current,
                    'progress_pct': round(completed / max(total, 1) * 100),
                })
    except Exception:
        pass
    return plans


@mind_bp.route('/')
def mind_page():
    state = _get_inner_state()
    knowledge = _get_knowledge_highlights()
    questions = _get_open_questions()
    dreams = _get_recent_dreams()
    plans = _get_active_plans()
    
    return render_template('mind.html',
                           state=state,
                           knowledge=knowledge,
                           questions=questions,
                           dreams=dreams,
                           plans=plans)
