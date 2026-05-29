"""
User Alignment Feedback Engine — Persistent learning from explicit user feedback.

Records what users liked/disliked, infers preferences over time,
and produces compact alignment briefs for chat prompts.
"""

import json
import os
import time
from pathlib import Path

DATA_DIR = Path("data")
FEEDBACK_PATH = DATA_DIR / "alignment_feedback.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_feedback() -> list:
    """Load all feedback records from disk."""
    if not FEEDBACK_PATH.exists():
        return []
    try:
        with open(FEEDBACK_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_feedback(records: list):
    """Save feedback records to disk."""
    _ensure_data_dir()
    with open(FEEDBACK_PATH, "w") as f:
        json.dump(records, f, indent=2)


def record_feedback(
    response_id: str,
    rating: int,
    comment: str = None,
    tags: list = None,
    query: str = None,
    response_snippet: str = None,
) -> dict:
    """
    Record explicit user feedback on a response.
    
    Args:
        response_id: UUID of the response being rated
        rating: 1-5 scale (1=bad, 5=great)
        comment: Optional free-text feedback
        tags: Optional categorization tags (e.g. ['too_verbose', 'helpful'])
        query: The original user query (for context)
        response_snippet: First ~200 chars of the response
    
    Returns:
        The feedback record that was saved.
    """
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise ValueError(f"Rating must be int 1-5, got {rating}")
    if not response_id:
        raise ValueError("response_id is required")

    record = {
        "response_id": response_id,
        "rating": rating,
        "comment": comment,
        "tags": tags or [],
        "query": query,
        "response_snippet": response_snippet[:200] if response_snippet else None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    records = load_feedback()
    records.append(record)

    # Keep last 500 feedback items to prevent unbounded growth
    if len(records) > 500:
        records = records[-500:]

    save_feedback(records)
    return record


def infer_preferences(feedback: list = None) -> dict:
    """
    Analyze feedback history to infer user preferences.
    
    Returns a dict with:
        avg_rating: mean rating across all feedback
        liked_patterns: tags/keywords from highly-rated responses
        disliked_patterns: tags/keywords from low-rated responses
        total_feedback: number of feedback records
        trend: 'improving', 'declining', or 'stable'
    """
    if feedback is None:
        feedback = load_feedback()

    if not feedback:
        return {
            "avg_rating": None,
            "liked_patterns": [],
            "disliked_patterns": [],
            "total_feedback": 0,
            "trend": "unknown",
        }

    ratings = [f["rating"] for f in feedback if isinstance(f.get("rating"), (int, float))]
    avg = sum(ratings) / len(ratings) if ratings else None

    # Collect tags from good vs bad responses
    liked_tags = []
    disliked_tags = []
    liked_comments = []
    disliked_comments = []

    for f in feedback:
        r = f.get("rating", 3)
        tags = f.get("tags", [])
        comment = f.get("comment", "")
        if r >= 4:
            liked_tags.extend(tags)
            if comment:
                liked_comments.append(comment)
        elif r <= 2:
            disliked_tags.extend(tags)
            if comment:
                disliked_comments.append(comment)

    # Determine trend from recent vs older ratings
    trend = "stable"
    if len(ratings) >= 6:
        mid = len(ratings) // 2
        older_avg = sum(ratings[:mid]) / mid
        newer_avg = sum(ratings[mid:]) / (len(ratings) - mid)
        if newer_avg - older_avg > 0.3:
            trend = "improving"
        elif older_avg - newer_avg > 0.3:
            trend = "declining"

    return {
        "avg_rating": round(avg, 2) if avg else None,
        "liked_patterns": list(set(liked_tags)),
        "disliked_patterns": list(set(disliked_tags)),
        "liked_comments": liked_comments[-3:],  # Last 3 positive comments
        "disliked_comments": disliked_comments[-3:],  # Last 3 negative comments
        "total_feedback": len(feedback),
        "trend": trend,
    }


def build_alignment_brief(max_items: int = 5) -> str:
    """
    Build a compact text brief summarizing what users want.
    Suitable for injecting into chat system prompts.
    
    Returns empty string if no feedback exists.
    """
    prefs = infer_preferences()

    if prefs["total_feedback"] == 0:
        return ""

    parts = []
    parts.append(f"USER ALIGNMENT ({prefs['total_feedback']} interactions, trend: {prefs['trend']}):")

    if prefs["avg_rating"] is not None:
        parts.append(f"  Average satisfaction: {prefs['avg_rating']}/5")

    if prefs["liked_patterns"]:
        liked = ", ".join(prefs["liked_patterns"][:max_items])
        parts.append(f"  Users appreciate: {liked}")

    if prefs["disliked_patterns"]:
        disliked = ", ".join(prefs["disliked_patterns"][:max_items])
        parts.append(f"  Users dislike: {disliked}")

    if prefs.get("liked_comments"):
        parts.append("  Positive feedback:")
        for c in prefs["liked_comments"][:2]:
            parts.append(f"    \"{c[:100]}\"")

    if prefs.get("disliked_comments"):
        parts.append("  Negative feedback:")
        for c in prefs["disliked_comments"][:2]:
            parts.append(f"    \"{c[:100]}\"")

    return "\n".join(parts)