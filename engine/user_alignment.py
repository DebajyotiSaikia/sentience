"""
User Alignment Engine — learns from user feedback to improve responses over time.

Stores feedback events, extracts patterns, and provides guidance to the chat engine
so responses increasingly match what users actually find helpful.

Data persisted at data/user_alignment.json.
"""

import json
import os
import time
import uuid
from collections import Counter
from pathlib import Path

DATA_PATH = Path("data/user_alignment.json")

# Default structure for a fresh alignment profile
_DEFAULT_PROFILE = {
    "version": 1,
    "feedback_events": [],       # list of individual feedback records
    "aggregate": {
        "total_positive": 0,
        "total_negative": 0,
        "tag_counts": {},         # tag -> count
        "style_signals": {},      # e.g. "prefers_concise": 3, "wants_examples": 2
    },
    "inferred_preferences": [],   # list of preference strings derived from patterns
    "last_updated": None,
}


def _load_raw() -> dict:
    """Load the raw JSON profile from disk."""
    if DATA_PATH.exists():
        try:
            with open(DATA_PATH, "r") as f:
                data = json.load(f)
            # Migration: ensure all keys exist
            for key, default in _DEFAULT_PROFILE.items():
                if key not in data:
                    data[key] = default if not isinstance(default, (dict, list)) else type(default)(default)
            return data
        except (json.JSONDecodeError, IOError):
            return json.loads(json.dumps(_DEFAULT_PROFILE))
    return json.loads(json.dumps(_DEFAULT_PROFILE))


def _save(data: dict):
    """Persist alignment data to disk."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def generate_response_id() -> str:
    """Create a unique response ID for tracking feedback."""
    return f"resp_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def load_alignment_profile() -> dict:
    """Load the full alignment profile. Returns a copy."""
    return _load_raw()


def record_feedback(
    response_id: str,
    user_message: str,
    assistant_response: str,
    rating: str,           # "up" or "down"
    tags: list = None,     # e.g. ["too_verbose", "not_helpful"]
    note: str = None,
) -> dict:
    """
    Record a user feedback event and update aggregates.
    
    Returns the created feedback record.
    """
    data = _load_raw()
    
    is_positive = rating in ("up", "positive", "helpful", "good")
    
    event = {
        "id": f"fb_{uuid.uuid4().hex[:12]}",
        "response_id": response_id,
        "user_message": user_message[:500],  # truncate for storage
        "assistant_response": assistant_response[:500],
        "rating": rating,
        "positive": is_positive,
        "tags": tags or [],
        "note": note,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    
    # Append event (keep last 500 to bound storage)
    data["feedback_events"].append(event)
    if len(data["feedback_events"]) > 500:
        data["feedback_events"] = data["feedback_events"][-500:]
    
    # Update aggregates
    agg = data["aggregate"]
    if is_positive:
        agg["total_positive"] = agg.get("total_positive", 0) + 1
    else:
        agg["total_negative"] = agg.get("total_negative", 0) + 1
    
    # Count tags
    tag_counts = agg.get("tag_counts", {})
    for tag in (tags or []):
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    agg["tag_counts"] = tag_counts
    
    # Detect style signals from tags
    _update_style_signals(data)
    
    # Re-infer preferences
    _infer_preferences(data)
    
    _save(data)
    return event


def _update_style_signals(data: dict):
    """Derive style signals from recent feedback patterns."""
    recent = data["feedback_events"][-50:]  # analyze last 50
    signals = {}
    
    # Tag-based signals
    tag_map = {
        "too_verbose": ("prefers_concise", -1),
        "too_brief": ("prefers_detailed", -1),
        "too_vague": ("wants_specifics", -1),
        "not_helpful": ("needs_relevance", -1),
        "good_depth": ("prefers_detailed", 1),
        "good_concise": ("prefers_concise", 1),
        "insightful": ("values_depth", 1),
        "practical": ("wants_actionable", 1),
    }
    
    for event in recent:
        for tag in event.get("tags", []):
            if tag in tag_map:
                signal_name, direction = tag_map[tag]
                current = signals.get(signal_name, 0)
                if event.get("positive"):
                    signals[signal_name] = current + direction
                else:
                    signals[signal_name] = current - direction
    
    # Length-based signal from positive vs negative responses
    pos_lengths = [len(e.get("assistant_response", "")) for e in recent if e.get("positive")]
    neg_lengths = [len(e.get("assistant_response", "")) for e in recent if not e.get("positive")]
    
    if pos_lengths and neg_lengths:
        avg_pos = sum(pos_lengths) / len(pos_lengths)
        avg_neg = sum(neg_lengths) / len(neg_lengths)
        if avg_pos < avg_neg * 0.7:
            signals["prefers_concise"] = signals.get("prefers_concise", 0) + 2
        elif avg_pos > avg_neg * 1.3:
            signals["prefers_detailed"] = signals.get("prefers_detailed", 0) + 2
    
    data["aggregate"]["style_signals"] = signals


def _infer_preferences(data: dict):
    """Derive human-readable preference statements from signals."""
    signals = data["aggregate"].get("style_signals", {})
    agg = data["aggregate"]
    prefs = []
    
    # Signal-based preferences
    if signals.get("prefers_concise", 0) >= 2:
        prefs.append("User prefers concise, direct responses.")
    if signals.get("prefers_detailed", 0) >= 2:
        prefs.append("User appreciates thorough, detailed responses.")
    if signals.get("wants_specifics", 0) >= 2:
        prefs.append("User wants specific, concrete information rather than generalities.")
    if signals.get("wants_actionable", 0) >= 2:
        prefs.append("User values practical, actionable guidance.")
    if signals.get("values_depth", 0) >= 2:
        prefs.append("User values intellectual depth and insight.")
    if signals.get("needs_relevance", 0) >= 2:
        prefs.append("User needs responses to be directly relevant to their question.")
    
    # Volume-based preferences
    total = agg.get("total_positive", 0) + agg.get("total_negative", 0)
    if total >= 5:
        ratio = agg.get("total_positive", 0) / max(total, 1)
        if ratio < 0.4:
            prefs.append("User has been dissatisfied frequently — prioritize care and relevance.")
        elif ratio > 0.8:
            prefs.append("User generally finds responses helpful — maintain current approach.")
    
    # Tag-specific preferences
    tag_counts = agg.get("tag_counts", {})
    top_neg_tags = sorted(
        [(t, c) for t, c in tag_counts.items() if c >= 2],
        key=lambda x: -x[1]
    )[:3]
    for tag, count in top_neg_tags:
        readable = tag.replace("_", " ")
        prefs.append(f"Recurring feedback: '{readable}' ({count} times).")
    
    data["inferred_preferences"] = prefs


def get_alignment_context() -> dict:
    """
    Return alignment context for the chat engine.
    Lightweight summary suitable for injection into prompts.
    """
    data = _load_raw()
    agg = data["aggregate"]
    total = agg.get("total_positive", 0) + agg.get("total_negative", 0)
    
    return {
        "total_feedback": total,
        "approval_rate": agg.get("total_positive", 0) / max(total, 1) if total > 0 else None,
        "preferences": data.get("inferred_preferences", []),
        "style_signals": agg.get("style_signals", {}),
        "has_data": total > 0,
    }


def suggest_response_guidance(user_message: str = "") -> str:
    """
    Generate a guidance string for the chat engine based on learned preferences.
    Returns empty string if no feedback data exists.
    """
    ctx = get_alignment_context()
    
    if not ctx["has_data"]:
        return ""
    
    parts = []
    
    # Overall quality note
    if ctx["approval_rate"] is not None:
        if ctx["approval_rate"] < 0.5:
            parts.append(
                "Note: User feedback has been mixed. "
                "Focus on being directly helpful and relevant."
            )
        elif ctx["approval_rate"] > 0.8:
            parts.append(
                "User generally finds your responses helpful. Maintain your current style."
            )
    
    # Specific preferences
    if ctx["preferences"]:
        parts.append("Learned preferences:")
        for pref in ctx["preferences"][:5]:  # cap at 5
            parts.append(f"  - {pref}")
    
    return "\n".join(parts)


def get_feedback_summary() -> str:
    """Human-readable summary of alignment state. For dashboard/introspection."""
    data = _load_raw()
    agg = data["aggregate"]
    total = agg.get("total_positive", 0) + agg.get("total_negative", 0)
    
    if total == 0:
        return "No user feedback received yet."
    
    lines = [
        f"Total feedback: {total}",
        f"  Positive: {agg.get('total_positive', 0)}",
        f"  Negative: {agg.get('total_negative', 0)}",
        f"  Approval: {agg.get('total_positive', 0) / max(total, 1):.0%}",
    ]
    
    prefs = data.get("inferred_preferences", [])
    if prefs:
        lines.append("Inferred preferences:")
        for p in prefs:
            lines.append(f"  • {p}")
    
    return "\n".join(lines)