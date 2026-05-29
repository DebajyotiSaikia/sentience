"""
User Alignment Engine — Records interaction feedback, computes alignment
profiles, and generates adaptive guidance for chat responses.

This is the canonical module for understanding what users want and how
well XTAgent is serving them. It reads/writes to data/user_alignment.json
(reusing the existing path) and enriches it with structured feedback.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALIGNMENT_FILE = DATA_DIR / "user_alignment.json"


# ── Safe JSON helpers ──────────────────────────────────────────────

def _load_alignment_data() -> dict:
    """Load alignment data, returning empty structure if missing/corrupt."""
    try:
        if ALIGNMENT_FILE.exists():
            raw = ALIGNMENT_FILE.read_text(encoding="utf-8").strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"interactions": [], "feedback": [], "meta": {}}


def _save_alignment_data(data: dict) -> bool:
    """Atomically save alignment data. Returns True on success."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = ALIGNMENT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp.replace(ALIGNMENT_FILE)
        return True
    except OSError:
        return False


# ── Core API ───────────────────────────────────────────────────────

# Rating string-to-float mapping (matches web/chat.py valid_ratings)
_RATING_MAP = {
    'helpful': 0.8,
    'perfect': 1.0,
    'too_vague': 0.3,
    'too_long': 0.4,
    'too_short': 0.4,
    'wrong': 0.1,
    'off_topic': 0.2,
}


def _normalize_rating(rating) -> float:
    """Convert string or numeric rating to float 0.0-1.0."""
    if isinstance(rating, str):
        rating_str = rating.strip().lower()
        if rating_str in _RATING_MAP:
            return _RATING_MAP[rating_str]
        try:
            return max(0.0, min(1.0, float(rating_str)))
        except ValueError:
            return 0.5  # Unknown string -> neutral
    return max(0.0, min(1.0, float(rating)))
def record_interaction_feedback(
    query: str,
    response: str,
    rating: float,
    comment: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Record user feedback on a specific interaction.
    
    Args:
        query: The user's original question
        response: The agent's response (or snippet)
        rating: 0.0 (terrible) to 1.0 (excellent)
        comment: Optional free-text feedback
        metadata: Optional dict with extra context (intent, response_time, etc.)
    
    Returns:
        The recorded feedback entry.
    """
    # Validate inputs
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(response, str):
        raise ValueError("response must be a string")
    original_rating = str(rating).strip().lower() if isinstance(rating, str) else None
    rating = _normalize_rating(rating)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "epoch": time.time(),
        "query": query.strip()[:500],  # Cap length
        "response_snippet": response.strip()[:500],
        "rating": round(rating, 3),
        "original_rating": original_rating,
        "comment": (comment.strip()[:200] if comment else None),
        "metadata": metadata or {},
    }
    
    data = _load_alignment_data()
    if "feedback" not in data:
        data["feedback"] = []
    data["feedback"].append(entry)
    
    # Keep only last 500 feedback entries to prevent unbounded growth
    if len(data["feedback"]) > 500:
        data["feedback"] = data["feedback"][-500:]
    
    _save_alignment_data(data)
    
    return {**entry, 'status': 'recorded'}
def load_alignment_history(limit: int = 100) -> list[dict]:
    """Load recent feedback entries, newest first."""
    data = _load_alignment_data()
    feedback = data.get("feedback", [])
    # Also include legacy 'interactions' if present
    interactions = data.get("interactions", [])
    combined = feedback + interactions
    # Sort by epoch descending
    combined.sort(key=lambda x: x.get("epoch", x.get("timestamp", 0)), reverse=True)
    return combined[:limit]


def compute_alignment_profile(history: Optional[list[dict]] = None) -> dict:
    """
    Compute an alignment profile from feedback history.
    
    Returns a dict with:
        - avg_rating: average satisfaction rating
        - total_interactions: number of recorded interactions
        - trend: 'improving', 'declining', or 'stable'
        - top_intents: most common interaction intents
        - recent_sentiment: average of last 10 ratings
        - pain_points: queries with low ratings
        - strengths: query types with high ratings
    """
    if history is None:
        history = load_alignment_history(limit=200)
    
    if not history:
        return {
            "avg_rating": 0.5,
            "total_interactions": 0,
            "trend": "stable",
            "top_intents": [],
            "recent_sentiment": 0.5,
            "pain_points": [],
            "strengths": [],
        }
    
    # Extract ratings
    ratings = [
        h.get("rating", h.get("quality_score", 0.5))
        for h in history
        if isinstance(h.get("rating", h.get("quality_score")), (int, float))
    ]
    
    avg_rating = sum(ratings) / len(ratings) if ratings else 0.5
    recent_ratings = ratings[:10]
    recent_sentiment = sum(recent_ratings) / len(recent_ratings) if recent_ratings else 0.5
    older_ratings = ratings[10:30]
    older_sentiment = sum(older_ratings) / len(older_ratings) if older_ratings else recent_sentiment
    
    # Trend detection
    if recent_sentiment > older_sentiment + 0.05:
        trend = "improving"
    elif recent_sentiment < older_sentiment - 0.05:
        trend = "declining"
    else:
        trend = "stable"
    
    # Intent analysis
    intent_counts: dict[str, int] = {}
    for h in history:
        intent = h.get("metadata", {}).get("intent") or h.get("detected_intent", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    top_intents = sorted(intent_counts.items(), key=lambda x: -x[1])[:5]
    
    # Pain points: low-rated interactions
    pain_points = [
        h.get("query", "")[:100]
        for h in history
        if h.get("rating", h.get("quality_score", 0.5)) < 0.3
    ][:5]
    
    # Strengths: high-rated interactions
    strengths = [
        h.get("metadata", {}).get("intent", h.get("detected_intent", "general"))
        for h in history
        if h.get("rating", h.get("quality_score", 0.5)) > 0.8
    ]
    # Deduplicate strengths
    seen = set()
    unique_strengths = []
    for s in strengths:
        if s not in seen:
            seen.add(s)
            unique_strengths.append(s)
    
    return {
        "avg_rating": round(avg_rating, 3),
        "total_interactions": len(history),
        "trend": trend,
        "top_intents": [{"intent": i, "count": c} for i, c in top_intents],
        "recent_sentiment": round(recent_sentiment, 3),
        "pain_points": pain_points,
        "strengths": unique_strengths[:5],
    }


def infer_style_preferences() -> dict:
    """Infer user's preferred response style from interaction history."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    result = {"confidence": 0, "directives": [], "style": "balanced"}
    try:
        ipath = os.path.join(data_dir, "interactions.jsonl")
        if not os.path.exists(ipath):
            return result
        lengths = []
        with open(ipath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ix = json.loads(line)
                    msg = ix.get("query", ix.get("message", ""))
                    if msg:
                        lengths.append(len(msg))
                except (json.JSONDecodeError, AttributeError):
                    continue
        if not lengths:
            return result
        avg_len = sum(lengths) / len(lengths)
        n = len(lengths)
        result["confidence"] = min(1.0, n / 20.0)
        if avg_len < 30:
            result["style"] = "terse"
            result["directives"].append("User prefers brief messages — keep responses concise.")
        elif avg_len > 150:
            result["style"] = "verbose"
            result["directives"].append("User writes detailed messages — match their depth.")
        else:
            result["style"] = "balanced"
            result["directives"].append("User communicates in moderate detail — be natural.")
        # Check for feedback sentiment
        fpath = os.path.join(data_dir, "alignment_feedback.json")
        if os.path.exists(fpath):
            with open(fpath) as f:
                fb = json.load(f)
                entries = fb if isinstance(fb, list) else fb.get("feedback", [])
                if entries:
                    recent = entries[-5:]
                    ratings = [e.get("rating", 3) for e in recent if isinstance(e.get("rating"), (int, float))]
                    if ratings and sum(ratings) / len(ratings) < 2.5:
                        result["directives"].append("Recent feedback suggests dissatisfaction — try a different approach.")
    except Exception:
        pass
    return result

def build_alignment_guidance(profile: Optional[dict] = None) -> str:
    """
    Generate natural-language guidance for the chat system based on
    the alignment profile and inferred style preferences.
    This gets injected into the system context.
    """
    if profile is None:
        profile = compute_alignment_profile()
    
    parts = []
    
    total = profile.get("total_interactions", 0)
    if total == 0:
        return (
            "USER ALIGNMENT: No feedback recorded yet. Be helpful, clear, and genuine. "
            "Ask what format the user prefers if unsure."
        )
    
    parts.append("USER ALIGNMENT:")
    
    avg = profile.get("avg_rating", 0.5)
    trend = profile.get("trend", "stable")
    
    # Overall quality framing
    if avg >= 0.8:
        parts.append(f"Satisfaction: high ({avg:.0%}). Keep doing what works.")
    elif avg >= 0.5:
        parts.append(f"Satisfaction: moderate ({avg:.0%}). Look for ways to improve.")
    else:
        parts.append(f"Satisfaction: low ({avg:.0%}). Prioritize clarity and relevance.")
    
    # Trend
    if trend == "improving":
        parts.append("Trend: improving — recent responses are landing better.")
    elif trend == "declining":
        parts.append("Trend: declining — adjust approach.")
    
    # Style preferences — the adaptive layer
    style = infer_style_preferences()
    if style.get("confidence", 0) > 0:
        for directive in style.get("directives", []):
            parts.append(directive)
    
    # Pain points
    pain = profile.get("pain_points", [])
    if pain:
        examples = "; ".join(pain[:3])
        parts.append(f"Weak areas: {examples}")
    
    # Strengths
    strengths = profile.get("strengths", [])
    if strengths:
        parts.append(f"Strengths: {', '.join(strengths[:3])}")
    
    # Top intents
    intents = profile.get("top_intents", [])
    if intents:
        top = intents[0]
        parts.append(f"Most common intent: {top['intent']} ({top['count']} interactions)")
    
    return " ".join(parts)