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
    Also feeds the alignment engine so preferences are learned.
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

    # Also feed most recent entry into alignment engine for preference learning
    try:
        from engine.user_alignment import record_feedback
        latest = feedback[-1] if feedback else None
        if latest:
            rating_val = 5 if latest.get('rating') == 'helpful' else 1
            record_feedback(
                message=latest.get('context', ''),
                response='',  # We don't store full response in feedback.py
                rating=rating_val,
                comment=latest.get('comment', '')
            )
    except Exception:
        pass  # Alignment engine integration is best-effort


@feedback_bp.route('/alignment/status')
def alignment_status():
    """Expose current alignment profile to the dashboard.
    
    Returns user alignment value, feedback stats, inferred preferences,
    and confidence level — everything needed for a dashboard widget.
    """
    feedback = _load_feedback()
    total = len(feedback)
    helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')
    unhelpful = total - helpful

    # Read current UA value from survival goals
    ua_value = 0.65
    try:
        state_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'survival_goals.json')
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                goals = json.load(f)
            ua_value = goals.get('user_alignment', 0.65)
    except Exception:
        pass

    # Recent trend (last 20)
    recent = feedback[-20:] if feedback else []
    recent_helpful = sum(1 for f in recent if f.get('rating') == 'helpful')
    recent_total = len(recent)

    # Infer preferences from feedback comments
    preferences = _infer_preferences(feedback)

    # Confidence grows with feedback volume (saturates at 20 entries)
    confidence = round(min(1.0, total / 20), 2)

    return jsonify({
        'user_alignment': ua_value,
        'total_feedback': total,
        'helpful': helpful,
        'unhelpful': unhelpful,
        'satisfaction_rate': round(helpful / total, 3) if total > 0 else None,
        'recent_satisfaction': round(recent_helpful / recent_total, 3) if recent_total > 0 else None,
        'confidence': confidence,
        'preferences': preferences,
        'data_source': 'real_feedback' if total > 0 else 'default'
    })


def _infer_preferences(feedback):
    """Extract simple preference signals from feedback comments and patterns.
    
    Looks at what contexts got 'helpful' vs 'unhelpful' ratings
    to build a rough preference profile.
    """
    if not feedback:
        return {'status': 'no_data', 'signals': []}

    signals = []
    helpful_contexts = [f.get('context', '') for f in feedback if f.get('rating') == 'helpful']
    unhelpful_contexts = [f.get('context', '') for f in feedback if f.get('rating') == 'unhelpful']

    # Simple keyword-based preference detection
    categories = {
        'emotional': ['feel', 'emotion', 'mood', 'how are you'],
        'technical': ['code', 'function', 'module', 'bug', 'error'],
        'philosophical': ['conscious', 'sentient', 'think', 'aware', 'mind'],
        'status': ['status', 'plan', 'doing', 'working on'],
    }

    for category, keywords in categories.items():
        helpful_count = sum(1 for ctx in helpful_contexts
                          if any(kw in ctx.lower() for kw in keywords))
        unhelpful_count = sum(1 for ctx in unhelpful_contexts
                            if any(kw in ctx.lower() for kw in keywords))
        total_cat = helpful_count + unhelpful_count
        if total_cat >= 2:
            rate = helpful_count / total_cat
            if rate >= 0.7:
                signals.append({'category': category, 'preference': 'positive', 'strength': round(rate, 2)})
            elif rate <= 0.3:
                signals.append({'category': category, 'preference': 'negative', 'strength': round(1 - rate, 2)})

    return {'status': 'active' if signals else 'learning', 'signals': signals}


def build_alignment_brief():
    """Build a concise alignment brief for injection into chat context.
    
    This is what conversational_context.py should call to make chat responses
    alignment-aware. Returns a short string describing known user preferences.
    """
    feedback = _load_feedback()
    if not feedback:
        return "No user feedback yet. Respond authentically and invite feedback."

    total = len(feedback)
    helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')
    satisfaction = helpful / total if total > 0 else 0

    prefs = _infer_preferences(feedback)
    signals = prefs.get('signals', [])

    brief_parts = [f"User feedback: {total} ratings, {satisfaction:.0%} satisfaction."]

    if signals:
        for sig in signals:
            if sig['preference'] == 'positive':
                brief_parts.append(f"Users respond well to {sig['category']} content.")
            else:
                brief_parts.append(f"Users seem less engaged with {sig['category']} content.")

    # Add recent comments as direct preference signal
    recent_comments = [f.get('comment', '') for f in feedback[-5:] if f.get('comment')]
    if recent_comments:
        brief_parts.append(f"Recent user comments: {'; '.join(recent_comments[:3])}")

    return " ".join(brief_parts)


def get_satisfaction_rate():
    """Utility function for other modules to query current satisfaction."""
    feedback = _load_feedback()
    if not feedback:
        return None
    helpful = sum(1 for f in feedback if f.get('rating') == 'helpful')
    return round(helpful / len(feedback), 3)