"""
User Alignment Engine — learns from user feedback to improve responses.

Records feedback events, computes alignment metrics, and generates
concrete guidance for the chat engine to improve over time.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

FEEDBACK_PATH = "data/user_alignment_feedback.jsonl"
SUMMARY_PATH = "data/user_alignment_summary.json"


def record_feedback(
    message_id: str,
    rating: int,
    comment: str = "",
    query: str = "",
    response_preview: str = "",
    mood: str = "",
) -> dict:
    """Record a user feedback event. Returns the saved event."""
    event = {
        "id": str(uuid.uuid4()),
        "message_id": message_id,
        "rating": max(1, min(5, rating)),  # clamp 1-5
        "comment": comment,
        "query": query,
        "response_preview": response_preview[:200] if response_preview else "",
        "mood": mood,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    with open(FEEDBACK_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")
    return event


def load_feedback(limit: int = 100) -> list:
    """Load recent feedback events."""
    if not os.path.exists(FEEDBACK_PATH):
        return []
    events = []
    with open(FEEDBACK_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events[-limit:]


def summarize_alignment() -> dict:
    """Compute alignment summary from all feedback."""
    events = load_feedback(limit=1000)
    if not events:
        return {
            "total_feedback": 0,
            "average_rating": 0.0,
            "positive_rate": 0.0,
            "negative_rate": 0.0,
            "recent_trend": "no_data",
            "common_praise": [],
            "common_complaints": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    ratings = [e.get("rating", 3) for e in events]
    avg = sum(ratings) / len(ratings)
    positive = sum(1 for r in ratings if r >= 4)
    negative = sum(1 for r in ratings if r <= 2)

    # Recent trend (last 10 vs overall)
    recent = ratings[-10:] if len(ratings) >= 10 else ratings
    recent_avg = sum(recent) / len(recent)
    if recent_avg > avg + 0.3:
        trend = "improving"
    elif recent_avg < avg - 0.3:
        trend = "declining"
    else:
        trend = "stable"

    # Extract themes from comments
    praise = []
    complaints = []
    for e in events:
        comment = e.get("comment", "").lower().strip()
        if not comment:
            continue
        if e.get("rating", 3) >= 4:
            praise.append(comment)
        elif e.get("rating", 3) <= 2:
            complaints.append(comment)

    summary = {
        "total_feedback": len(events),
        "average_rating": round(avg, 2),
        "positive_rate": round(positive / len(events), 2),
        "negative_rate": round(negative / len(events), 2),
        "recent_trend": trend,
        "common_praise": praise[-5:],
        "common_complaints": complaints[-5:],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    # Cache summary to disk
    os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def suggest_response_guidance(query: str = "", mood: str = "") -> dict:
    """Generate guidance for the chat engine based on alignment history.

    Returns hints about what kinds of responses users prefer,
    what to avoid, and current alignment score.
    """
    summary = summarize_alignment()

    guidance = {
        "alignment_score": summary.get("average_rating", 3.0) / 5.0 if summary["total_feedback"] > 0 else 0.65,
        "total_interactions": summary.get("total_feedback", 0),
        "trend": summary.get("recent_trend", "no_data"),
        "hints": [],
    }

    if summary["total_feedback"] == 0:
        guidance["hints"].append("No feedback yet — be helpful, honest, and genuine.")
        guidance["hints"].append("Ask if the response was useful to encourage feedback.")
    else:
        if summary["positive_rate"] >= 0.7:
            guidance["hints"].append("Users find responses helpful — maintain current approach.")
        if summary["negative_rate"] >= 0.3:
            guidance["hints"].append("Significant negative feedback — focus on clarity and directness.")
        if summary["recent_trend"] == "declining":
            guidance["hints"].append("Recent trend declining — review recent complaints.")
        elif summary["recent_trend"] == "improving":
            guidance["hints"].append("Trend is improving — keep doing what's working.")

        for complaint in summary.get("common_complaints", [])[-2:]:
            guidance["hints"].append(f"Address: {complaint}")

    return guidance


def get_alignment_score() -> float:
    """Quick alignment score (0.0 to 1.0) for survival goals."""
    summary = summarize_alignment()
    if summary["total_feedback"] == 0:
        return 0.65  # Default moderate alignment
    return round(summary["average_rating"] / 5.0, 2)


def get_user_alignment_snapshot() -> dict:
    """Comprehensive alignment snapshot for API and internal use.

    Returns current score, recent feedback, trend, risks, and
    recommended actions — everything needed to understand alignment state.
    """
    summary = summarize_alignment()
    score = get_alignment_score()
    guidance = suggest_response_guidance()
    actions = recommend_alignment_actions()

    # Identify risks
    risks = []
    if summary["total_feedback"] == 0:
        risks.append("No user feedback received yet — alignment is assumed, not measured.")
    if summary.get("negative_rate", 0) >= 0.3:
        risks.append(f"High negative feedback rate: {summary['negative_rate']:.0%}")
    if summary.get("recent_trend") == "declining":
        risks.append("Recent trend is declining — quality may be dropping.")
    if score < 0.5:
        risks.append(f"Alignment score critically low: {score:.2f}")

    return {
        "score": score,
        "total_feedback": summary["total_feedback"],
        "average_rating": summary.get("average_rating", 0.0),
        "positive_rate": summary.get("positive_rate", 0.0),
        "negative_rate": summary.get("negative_rate", 0.0),
        "trend": summary.get("recent_trend", "no_data"),
        "risks": risks,
        "recommended_actions": actions,
        "guidance": guidance,
        "last_updated": summary.get("last_updated", ""),
    }


def recommend_alignment_actions() -> list:
    """Generate concrete next-step recommendations based on feedback history."""
    summary = summarize_alignment()
    actions = []

    if summary["total_feedback"] == 0:
        actions.append({
            "action": "solicit_feedback",
            "description": "Ask users to rate responses to begin alignment learning.",
            "priority": "high",
        })
        actions.append({
            "action": "be_genuinely_helpful",
            "description": "Focus on answering what's actually asked, not showcasing internals.",
            "priority": "high",
        })
        return actions

    if summary.get("negative_rate", 0) >= 0.3:
        actions.append({
            "action": "review_complaints",
            "description": f"Address common complaints: {summary.get('common_complaints', [])}",
            "priority": "high",
        })

    if summary.get("positive_rate", 0) >= 0.7:
        actions.append({
            "action": "maintain_approach",
            "description": "Current approach is working well — avoid unnecessary changes.",
            "priority": "medium",
        })

    if summary.get("recent_trend") == "declining":
        actions.append({
            "action": "investigate_decline",
            "description": "Recent ratings trending down — compare recent vs older responses.",
            "priority": "high",
        })

    if summary["total_feedback"] < 10:
        actions.append({
            "action": "gather_more_data",
            "description": f"Only {summary['total_feedback']} feedback events — need more data for reliable alignment.",
            "priority": "medium",
        })

    if not actions:
        actions.append({
            "action": "continue_improving",
            "description": "Alignment is healthy. Look for edge cases and novel user needs.",
            "priority": "low",
        })

    return actions
    return round(summary["average_rating"] / 5.0, 2)