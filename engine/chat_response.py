"""
Chat Response — Wrapper that enriches chat responses with metadata.

Every response gets a stable ID for feedback tracking. Feedback flows
through to user_alignment for learning and improvement.
"""

import uuid
from datetime import datetime, timezone

from engine.chat_engine import generate_response, classify_intent
from engine import user_alignment


def generate_response_with_metadata(query: str) -> dict:
    """Generate a chat response enriched with metadata and a feedback ID."""
    response_id = str(uuid.uuid4())
    intent = classify_intent(query)

    # Get alignment guidance to potentially shape responses
    guidance = user_alignment.suggest_response_guidance()

    # Generate the core response
    response_text = generate_response(query)

    # Build enriched result
    result = {
        "response_id": response_id,
        "query": query,
        "intent": intent,
        "response": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guidance_applied": guidance.get("style_hints", []) if guidance else [],
    }

    return result


def submit_feedback(
    response_id: str,
    rating: int,
    comment: str = "",
    query: str = "",
    response_preview: str = "",
) -> dict:
    """Submit feedback for a specific response. Routes to user_alignment."""
    if not response_id:
        return {"status": "error", "message": "response_id is required"}
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return {"status": "error", "message": "rating must be integer 1-5"}

    event = user_alignment.record_feedback(
        message_id=response_id,
        rating=rating,
        comment=comment,
        query=query,
        response_preview=response_preview,
    )

    return {
        "status": "ok",
        "feedback_id": event["id"],
        "message": "Feedback recorded. Thank you.",
    }


def get_alignment_status() -> dict:
    """Get current alignment metrics for API exposure."""
    summary = user_alignment.get_feedback_summary()
    guidance = user_alignment.suggest_response_guidance()
    return {
        "summary": summary,
        "guidance": guidance,
    }