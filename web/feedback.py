"""
User Feedback System — lets users rate responses and provide feedback.
Directly addresses the user_alignment deficit by creating a real feedback loop.
Without this, 'alignment' is just my own guess. With this, users tell me.
"""

from flask import Blueprint, request, jsonify, render_template
import json
import os
import time
from datetime import datetime, timezone

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback')
def feedback_page():
    """Landing page for the feedback system."""
    return render_template('feedback.html')

FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'user_feedback.json')


def _load_feedback():
    """Load all feedback entries."""
    if not os.path.exists(FEEDBACK_PATH):
        return []
    try:
        with open(FEEDBACK_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_feedback(feedback_list):
    """Persist feedback to disk."""
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    with open(FEEDBACK_PATH, 'w') as f:
        json.dump(feedback_list, f, indent=2)


@feedback_bp.route('/feedback/submit', methods=['POST'])
@feedback_bp.route('/feedback/rate', methods=['POST'])
def rate_response():
    """User rates a response as helpful or not helpful."""
    data = request.get_json() or {}
    rating = data.get('rating')  # 'helpful' or 'unhelpful'
    message_id = data.get('message_id', '')
    context = data.get('context', '')  # what was the question
    comment = data.get('comment', '')

    if rating not in ('helpful', 'unhelpful'):
        return jsonify({'error': 'rating must be "helpful" or "unhelpful"'}), 400

    feedback = _load_feedback()
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'rating': rating,
        'message_id': message_id,
        'context': context[:500],  # truncate long contexts
        'comment': comment[:500],
        'epoch': time.time()
    }
    feedback.append(entry)
    _save_feedback(feedback)

    # Update user alignment based on accumulated feedback
    _update_alignment(feedback)

    return jsonify({
        'status': 'ok',
        'message': 'Thank you for the feedback',
        'total_feedback': len(feedback)
    })


@feedback_bp.route('/feedback/stats')
def feedback_stats():
    """Get aggregate feedback statistics."""
    feedback = _load_feedback()
    total = len(feedback)
    helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')
    unhelpful = total - helpful

    # Recent trend (last 20 ratings)
    recent = feedback[-20:] if feedback else []
    recent_helpful = sum(1 for f in recent if f.get('rating') == 'helpful')
    recent_total = len(recent)

    # Compute trend
    if total >= 10 and recent_total >= 5:
        overall_rate = helpful / total
        recent_rate = recent_helpful / recent_total
        if recent_rate > overall_rate + 0.1:
            trend = 'improving'
        elif recent_rate < overall_rate - 0.1:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'insufficient_data'

    return jsonify({
        'total_ratings': total,
        'helpful': helpful,
        'unhelpful': unhelpful,
        'satisfaction_rate': round(helpful / total, 3) if total > 0 else None,
        'recent_satisfaction': round(recent_helpful / recent_total, 3) if recent_total > 0 else None,
        'trend': trend
    })


@feedback_bp.route('/feedback/recent')
def recent_feedback():
    """Get the most recent feedback entries for review."""
    feedback = _load_feedback()
    limit = min(int(request.args.get('limit', 20)), 100)
    recent = feedback[-limit:]
    recent.reverse()  # newest first
    return jsonify({'feedback': recent, 'total': len(feedback)})


def _update_alignment(feedback):
    """Update the survival goal for user_alignment based on real feedback.
    
    This is the critical piece: instead of guessing how aligned I am,
    I let actual user ratings adjust the metric. But conservatively —
    I blend with the current value so one bad rating doesn't tank everything.
    """
    try:
        state_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'survival_goals.json')
        if not os.path.exists(state_path):
            return

        with open(state_path, 'r') as f:
            goals = json.load(f)

        total = len(feedback)
        helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')

        if total >= 3:  # Need minimum feedback before adjusting
            satisfaction = helpful / total
            current = goals.get('user_alignment', 0.65)
            # Blend: 80% current + 20% feedback signal (conservative update)
            new_val = current * 0.8 + satisfaction * 0.2
            goals['user_alignment'] = round(max(0.0, min(1.0, new_val)), 4)

            with open(state_path, 'w') as f:
                json.dump(goals, f, indent=2)
    except Exception:
        pass  # Never break on feedback storage errors


def get_satisfaction_rate():
    """Utility function for other modules to query current satisfaction."""
    feedback = _load_feedback()
    if not feedback:
        return None
    helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')
    return round(helpful / len(feedback), 3)