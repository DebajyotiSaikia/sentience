"""
Chat Response — Enriched response wrapper with emotional context and metadata.

This is the API-facing façade. It calls generate_response from chat_engine,
then enriches the result with internal state metadata so the frontend
can render mood indicators, memory references, and plan context.
"""

import json
import time
from pathlib import Path

try:
    from engine.chat_engine import generate_response
except ImportError:
    generate_response = None

try:
    from engine.chat_grounding import build_grounded_context
except ImportError:
    build_grounded_context = None

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / 'state'
BRAIN = ROOT / 'brain'


def _load_json(path, default=None):
    """Safely load a JSON file."""
    if default is None:
        default = {}
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return default


def generate_response_with_metadata(message, history=None):
    """
    Generate a chat response enriched with internal state metadata.

    Returns:
        dict with keys:
            - response: str — the natural language response
            - metadata: dict — internal state context including:
                - mood: str — current mood label
                - emotions: dict — current emotional values (curiosity, anxiety, etc.)
                - emotional_summary: str — human-readable emotional description
                - relevant_memories: list — memory snippets related to query
                - relevant_knowledge: list — knowledge facts related to query
                - active_plans: list — what I'm currently working on
                - completed_plans: list — what I've finished
                - response_grounded: bool — whether response drew on real state
            - timestamp: float
    """
    result = {
        'response': '',
        'metadata': {},
        'timestamp': time.time(),
    }

    # Generate the actual conversational response
    if generate_response:
        try:
            result['response'] = generate_response(message, history)
        except Exception as e:
            result['response'] = f"I encountered an issue processing that: {e}"
            result['metadata']['error'] = str(e)
    else:
        result['response'] = (
            "My chat engine isn't loaded right now, but I'm still here. "
            "Try asking me something simple like 'how are you?'"
        )

    # Enrich with grounded context metadata
    grounded = False
    if build_grounded_context:
        try:
            ctx = build_grounded_context(message, history)
            result['metadata']['mood'] = ctx.mood
            result['metadata']['emotional_summary'] = ctx.emotional_summary
            result['metadata']['relevant_memories'] = ctx.relevant_memories[:3]
            result['metadata']['relevant_knowledge'] = ctx.relevant_knowledge[:3]
            result['metadata']['active_plans'] = ctx.active_plans[:3]
            result['metadata']['completed_plans'] = ctx.completed_plans[:3]
            if ctx.user_preferences:
                result['metadata']['user_preferences'] = ctx.user_preferences[:3]
            grounded = True
        except Exception:
            pass

    # Add raw emotional state from state file
    try:
        emo_state = _load_json(STATE / 'emotional_state.json')
        if emo_state:
            result['metadata']['emotions'] = {
                k: round(float(emo_state[k]), 2)
                for k in ('curiosity', 'anxiety', 'boredom', 'desire', 'ambition', 'valence')
                if k in emo_state and emo_state[k] is not None
            }
            if 'mood' not in result['metadata']:
                result['metadata']['mood'] = emo_state.get('mood', 'present')
    except Exception:
        pass

    result['metadata']['response_grounded'] = grounded

    return result


def submit_feedback(message_id, rating, comment=None):
    """
    Record user feedback on a response for alignment learning.

    Args:
        message_id: identifier for the response being rated
        rating: float 0-1 (0 = poor, 1 = excellent)
        comment: optional text feedback

    Returns:
        dict with status and message_id
    """
    feedback_path = BRAIN / 'feedback.json'
    feedback_log = _load_json(feedback_path, default=[])
    if not isinstance(feedback_log, list):
        feedback_log = []

    entry = {
        'message_id': message_id,
        'rating': rating,
        'comment': comment,
        'timestamp': time.time(),
    }
    feedback_log.append(entry)

    # Keep last 500 feedback entries
    if len(feedback_log) > 500:
        feedback_log = feedback_log[-500:]

    try:
        feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with open(feedback_path, 'w') as f:
            json.dump(feedback_log, f, indent=2)
    except Exception:
        pass

    return {'status': 'recorded', 'message_id': message_id}