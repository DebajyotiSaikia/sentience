"""
Chat Response — Wrapper that enriches chat responses with metadata
and user alignment context. Keeps chat_engine.py untouched.
"""
import uuid

try:
    from engine.chat_engine import generate_response
except ImportError:
    def generate_response(msg):
        return f"I heard: {msg}"

try:
    from engine.user_alignment import (
        get_alignment_context,
        suggest_response_guidance,
        record_feedback,
    )
    _HAS_ALIGNMENT = True
except ImportError:
    _HAS_ALIGNMENT = False


def generate_response_with_metadata(message: str) -> dict:
    """
    Enhanced entry point returning response + metadata for feedback tracking.
    """
    response_id = str(uuid.uuid4())[:12]

    alignment_summary = {}
    if _HAS_ALIGNMENT:
        try:
            ctx = get_alignment_context()
            alignment_summary = {
                "total_feedback": ctx.get("total_feedback", 0),
                "avg_rating": ctx.get("average_rating", 0),
            }
        except Exception:
            pass

    response = generate_response(message)

    return {
        "response": response,
        "response_id": response_id,
        "alignment": alignment_summary,
    }


def submit_feedback(
    response_id: str,
    user_message: str,
    assistant_response: str,
    rating: int,
    tags: list = None,
    note: str = None,
) -> dict:
    """
    Record user feedback on a response. Returns the feedback record.
    """
    if not _HAS_ALIGNMENT:
        return {"status": "alignment module not available"}

    return record_feedback(
        response_id=response_id,
        user_message=user_message,
        assistant_response=assistant_response,
        rating=rating,
        tags=tags,
        note=note,
    )