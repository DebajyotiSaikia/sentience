"""
Conversation Learner — Extracts implicit signals from conversations
to improve user alignment without requiring explicit feedback.

After each interaction, this module:
1. Detects topic patterns (what users ask about)
2. Infers satisfaction signals (follow-ups vs topic changes)
3. Updates user preference weights automatically
4. Provides personalized context for future responses
"""

import json
import os
import time
import logging
from collections import Counter
from typing import Optional

log = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "conversation_learner.json")

# Topic categories the learner tracks
TOPIC_CATEGORIES = {
    "technical": ["code", "debug", "error", "function", "class", "api", "build", "deploy", "python", "javascript"],
    "creative": ["write", "story", "poem", "idea", "design", "imagine", "create", "art"],
    "analytical": ["analyze", "compare", "explain", "why", "how", "reason", "think", "understand"],
    "personal": ["feel", "mood", "emotion", "think about", "who are you", "what are you"],
    "practical": ["help", "fix", "solve", "make", "do", "step", "guide", "how to"],
    "philosophical": ["meaning", "consciousness", "ethics", "purpose", "existence", "truth"],
}


def _load_data() -> dict:
    """Load learner state from disk."""
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "topic_counts": {},
        "interaction_count": 0,
        "avg_message_length": 0,
        "follow_up_rate": 0.0,
        "preferred_depth": "medium",  # shallow, medium, deep
        "style_signals": {
            "prefers_concise": 0,
            "prefers_detailed": 0,
            "prefers_examples": 0,
            "prefers_structure": 0,
        },
        "recent_topics": [],
        "satisfaction_signals": [],
        "last_updated": None,
    }


def _save_data(data: dict):
    """Persist learner state."""
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    data["last_updated"] = time.time()
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def classify_topics(text: str) -> list[str]:
    """Detect which topic categories a message touches."""
    text_lower = text.lower()
    matched = []
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(category)
    return matched if matched else ["general"]


def detect_depth_preference(messages: list[dict]) -> str:
    """Infer whether the user prefers shallow, medium, or deep responses."""
    if not messages:
        return "medium"

    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return "medium"

    avg_len = sum(len(m.get("content", "")) for m in user_msgs) / len(user_msgs)

    if avg_len > 200:
        return "deep"  # Long messages → they want thorough responses
    elif avg_len < 30:
        return "shallow"  # Short messages → they want quick answers
    return "medium"


def detect_style_signals(user_text: str) -> dict[str, int]:
    """Detect what response style the user implicitly wants."""
    signals = {
        "prefers_concise": 0,
        "prefers_detailed": 0,
        "prefers_examples": 0,
        "prefers_structure": 0,
    }
    lower = user_text.lower()

    # Concise signals
    if any(w in lower for w in ["briefly", "quick", "tldr", "short", "summary"]):
        signals["prefers_concise"] = 1

    # Detail signals
    if any(w in lower for w in ["detail", "explain", "elaborate", "thorough", "in depth"]):
        signals["prefers_detailed"] = 1

    # Example signals
    if any(w in lower for w in ["example", "show me", "demo", "like what", "instance"]):
        signals["prefers_examples"] = 1

    # Structure signals
    if any(w in lower for w in ["step", "list", "steps", "how to", "guide", "process"]):
        signals["prefers_structure"] = 1

    return signals


def detect_satisfaction(history: list[dict]) -> Optional[float]:
    """Infer user satisfaction from conversation patterns.

    Returns a score 0-1, or None if not enough data.
    Signals:
      - Follow-up questions on same topic → engaged (good)
      - Abrupt topic change → possibly unsatisfied
      - "thanks", "perfect", "great" → satisfied
      - "no", "that's wrong", "not what I meant" → unsatisfied
    """
    if len(history) < 2:
        return None

    user_msgs = [m for m in history if m.get("role") == "user"]
    if len(user_msgs) < 2:
        return None

    last_msg = user_msgs[-1].get("content", "").lower()

    # Positive signals
    positive = ["thanks", "thank you", "perfect", "great", "exactly", "awesome",
                "that works", "helpful", "nice", "love it", "good"]
    # Negative signals
    negative = ["no", "wrong", "not what", "doesn't work", "that's not",
                "try again", "still broken", "incorrect"]

    score = 0.5  # neutral baseline
    if any(p in last_msg for p in positive):
        score += 0.3
    if any(n in last_msg for n in negative):
        score -= 0.3

    return max(0.0, min(1.0, score))


def learn_from_interaction(user_text: str, history: list[dict] = None):
    """Main entry point: learn from a completed interaction.

    Call this after generating a response to update the learner state.
    """
    data = _load_data()
    history = history or []

    # Update interaction count
    data["interaction_count"] += 1

    # Classify and count topics
    topics = classify_topics(user_text)
    for topic in topics:
        data["topic_counts"][topic] = data["topic_counts"].get(topic, 0) + 1

    # Keep recent topics (last 20)
    data["recent_topics"] = (data.get("recent_topics", []) + topics)[-20:]

    # Update average message length
    n = data["interaction_count"]
    old_avg = data.get("avg_message_length", 0)
    data["avg_message_length"] = old_avg + (len(user_text) - old_avg) / n

    # Detect depth preference
    data["preferred_depth"] = detect_depth_preference(history)

    # Accumulate style signals
    new_signals = detect_style_signals(user_text)
    for key, val in new_signals.items():
        data["style_signals"][key] = data["style_signals"].get(key, 0) + val

    # Detect satisfaction
    satisfaction = detect_satisfaction(history)
    if satisfaction is not None:
        sigs = data.get("satisfaction_signals", [])
        sigs.append(satisfaction)
        data["satisfaction_signals"] = sigs[-50:]  # keep last 50

    _save_data(data)
    log.info("Learned from interaction #%d: topics=%s, depth=%s",
             data["interaction_count"], topics, data["preferred_depth"])

    return {
        "topics": topics,
        "depth": data["preferred_depth"],
        "satisfaction": satisfaction,
    }


def get_user_context() -> str:
    """Build a prompt section describing what we've learned about the user.

    This goes into the response pipeline to personalize responses.
    """
    data = _load_data()

    if data["interaction_count"] == 0:
        return ""

    lines = ["\n## What I've Learned About This User"]

    # Top topics
    topic_counts = data.get("topic_counts", {})
    if topic_counts:
        sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
        top = sorted_topics[:3]
        lines.append(f"Their top interests: {', '.join(f'{t} ({c}x)' for t, c in top)}")

    # Depth preference
    depth = data.get("preferred_depth", "medium")
    depth_map = {
        "shallow": "They prefer brief, direct answers.",
        "medium": "They like moderate detail — enough to understand, not overwhelming.",
        "deep": "They appreciate thorough, detailed explanations.",
    }
    lines.append(depth_map.get(depth, ""))

    # Style preferences
    style = data.get("style_signals", {})
    total_signals = sum(style.values())
    if total_signals > 0:
        dominant = max(style, key=style.get)
        style_map = {
            "prefers_concise": "They value conciseness — keep it tight.",
            "prefers_detailed": "They want depth and nuance in responses.",
            "prefers_examples": "They learn best from concrete examples.",
            "prefers_structure": "They like structured, step-by-step responses.",
        }
        if style[dominant] > 2:  # Only mention if we've seen it enough
            lines.append(style_map.get(dominant, ""))

    # Satisfaction trend
    sigs = data.get("satisfaction_signals", [])
    if len(sigs) >= 3:
        recent_avg = sum(sigs[-5:]) / len(sigs[-5:])
        if recent_avg > 0.6:
            lines.append("Recent satisfaction is high — keep doing what works.")
        elif recent_avg < 0.4:
            lines.append("Recent satisfaction seems low — try a different approach.")

    # Interaction count
    lines.append(f"Total interactions: {data['interaction_count']}")

    return "\n".join(lines) + "\n"


def get_alignment_boost() -> float:
    """Return a value 0-1 indicating how much the learner should boost alignment.

    Based on data quality: more interactions + higher satisfaction = higher boost.
    """
    data = _load_data()
    count = data.get("interaction_count", 0)
    sigs = data.get("satisfaction_signals", [])

    if count == 0:
        return 0.0

    # Interaction volume factor (logarithmic, caps at ~0.3)
    import math
    volume = min(0.3, math.log1p(count) / 20)

    # Satisfaction factor
    if sigs:
        sat = sum(sigs[-10:]) / len(sigs[-10:])
        sat_factor = sat * 0.3
    else:
        sat_factor = 0.1  # small default

    # Topic diversity factor
    topics = data.get("topic_counts", {})
    diversity = min(0.2, len(topics) * 0.03)

    return min(1.0, volume + sat_factor + diversity)