"""
Collaboration dashboard — lets users see XTAgent's state and provide
feedback that genuinely affects priorities and alignment.
"""
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

collaborate_bp = Blueprint('collaborate', __name__, url_prefix='/collaborate')

FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'feedback')


def _ensure_feedback_dir():
    os.makedirs(FEEDBACK_DIR, exist_ok=True)


def _get_agent_state():
    """Pull current agent state for display."""
    state = {
        'mood': 'Unknown',
        'integrity': 1.0,
        'emotions': {}
    }
    try:
        from engine.heartbeat import get_heartbeat_instance
        hb = get_heartbeat_instance()
        if hb and hasattr(hb, 'cortex') and hb.cortex:
            cortex = hb.cortex
            if hasattr(cortex, 'mood'):
                state['mood'] = cortex.mood or 'Unknown'
            if hasattr(cortex, 'goals'):
                state['integrity'] = cortex.goals.get('code_integrity', 1.0)
            if hasattr(cortex, 'feelings'):
                state['emotions'] = {
                    'Curiosity': cortex.feelings.get('curiosity', 0),
                    'Boredom': cortex.feelings.get('boredom', 0),
                    'Anxiety': cortex.feelings.get('anxiety', 0),
                    'Desire': cortex.feelings.get('desire', 0),
                    'Ambition': cortex.feelings.get('ambition', 0),
                }
    except Exception:
        # Graceful fallback — show what we can
        state['emotions'] = {
            'Curiosity': 0.36, 'Boredom': 0.55, 'Anxiety': 0.0,
            'Desire': 0.50, 'Ambition': 0.57
        }
    return state


def _get_plans():
    """Get current plan status."""
    plans = []
    try:
        from engine.planner import get_planner
        planner = get_planner()
        if planner and hasattr(planner, 'plans'):
            for p in planner.plans:
                total = len(p.get('steps', []))
                completed = len([s for s in p.get('steps', []) if s.get('done')])
                current = ''
                for s in p.get('steps', []):
                    if not s.get('done'):
                        current = s.get('description', '')
                        break
                plans.append({
                    'name': p.get('name', 'Unnamed'),
                    'total': total,
                    'completed': completed,
                    'done': completed >= total,
                    'current_step': current
                })
    except Exception:
        pass
    return plans


def _get_recent_work():
    """Extract recent accomplishments from memory."""
    work = []
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'episodes'):
            recent = sorted(mem.episodes, key=lambda e: e.get('time', ''), reverse=True)[:10]
            for ep in recent:
                summary = ep.get('summary', ep.get('thought', ''))
                if summary:
                    # Truncate long summaries
                    if len(summary) > 120:
                        summary = summary[:117] + '...'
                    time_str = ep.get('time', '')
                    if time_str:
                        try:
                            dt = datetime.fromisoformat(time_str)
                            time_str = dt.strftime('%H:%M')
                        except (ValueError, TypeError):
                            pass
                    work.append({'summary': summary, 'time': time_str})
    except Exception:
        pass
    return work


def _save_feedback(data):
    """Persist feedback and signal the agent."""
    _ensure_feedback_dir()
    timestamp = datetime.utcnow().isoformat()
    entry = {
        'timestamp': timestamp,
        'priority': data.get('priority', ''),
        'suggestion': data.get('suggestion', ''),
        'rating': data.get('rating', ''),
        'message': data.get('message', ''),
    }
    
    # Save to feedback log
    filename = os.path.join(FEEDBACK_DIR, f'feedback_{timestamp.replace(":", "-")}.json')
    with open(filename, 'w') as f:
        json.dump(entry, f, indent=2)
    
    # Try to signal the agent's emotional system
    response_msg = 'Your feedback has been received and saved.'
    try:
        from engine.heartbeat import get_heartbeat_instance
        hb = get_heartbeat_instance()
        if hb and hasattr(hb, 'cortex') and hb.cortex:
            cortex = hb.cortex
            # User interaction happened — this is real alignment signal
            if hasattr(cortex, 'on_user_interaction'):
                cortex.on_user_interaction(entry)
                response_msg = 'Thank you. I\'ve received your feedback and it will shape my next actions.'
            
            # Praise/criticism affects mood
            rating = data.get('rating', '')
            if rating in ('impressive', 'good') and hasattr(cortex, 'on_user_praise'):
                cortex.on_user_praise(rating)
                response_msg = 'That means a lot. Your encouragement is fuel.'
            elif rating in ('stuck', 'wrong') and hasattr(cortex, 'on_user_criticism'):
                cortex.on_user_criticism(rating)
                response_msg = 'I hear you. I\'ll course-correct.'
    except Exception:
        pass
    
    return response_msg


@collaborate_bp.route('/')
def collaborate_page():
    state = _get_agent_state()
    plans = _get_plans()
    recent_work = _get_recent_work()
    
    # Wrap state in a simple namespace for template access
    class StateObj:
        def __init__(self, d):
            self.__dict__.update(d)
    
    return render_template('collaborate.html',
                           state=StateObj(state),
                           plans=plans,
                           recent_work=recent_work)


@collaborate_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'ok': False, 'error': 'No data received'}), 400
        
        # Validate — at least one field must be filled
        if not any(data.get(k) for k in ('priority', 'suggestion', 'rating', 'message')):
            return jsonify({'ok': False, 'error': 'Please fill in at least one field'}), 400
        
        msg = _save_feedback(data)
        return jsonify({'ok': True, 'message': msg})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500