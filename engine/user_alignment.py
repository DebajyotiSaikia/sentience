"""
User Alignment — Learns and applies user preferences to improve interactions.

Tracks explicit feedback, infers preferences from conversation patterns,
and provides alignment context for chat grounding.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime

DATA_PATH = Path("data/user_alignment.json")

_DEFAULT_PROFILE = {
    "created": None,
    "updated": None,
    "preferences": {
        "tone": [],          # e.g. ["direct", "warm"]
        "topics_liked": [],  # topics they engage with
        "topics_avoided": [],
        "verbosity": "medium",  # "brief", "medium", "detailed"
        "style_notes": []
    },
    "feedback": [],          # list of {timestamp, message_preview, rating, comment}
    "interaction_count": 0,
    "positive_patterns": [], # what worked well
    "negative_patterns": []  # what didn't work
}


def load_profile() -> dict:
    """Load the user alignment profile from disk."""
    if DATA_PATH.exists():
        try:
            with open(DATA_PATH) as f:
                profile = json.load(f)
            # Ensure all keys exist (forward compatibility)
            for key, default in _DEFAULT_PROFILE.items():
                if key not in profile:
                    profile[key] = default if not isinstance(default, (list, dict)) else type(default)(default)
            return profile
        except (json.JSONDecodeError, IOError):
            pass
    return _make_new_profile()


def _make_new_profile() -> dict:
    """Create a fresh profile."""
    import copy
    profile = copy.deepcopy(_DEFAULT_PROFILE)
    profile["created"] = datetime.utcnow().isoformat()
    profile["updated"] = profile["created"]
    return profile


def save_profile(profile: dict):
    """Persist the profile to disk."""
    profile["updated"] = datetime.utcnow().isoformat()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def record_feedback(message: str, response: str, rating: float = None, comment: str = None):
    """
    Record user feedback on a response.
    
    Args:
        message: The user's original message
        response: The agent's response
        rating: 0.0 to 1.0 quality rating (None if not provided)
        comment: Optional text feedback
    """
    profile = load_profile()
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "message_preview": message[:120] if message else "",
        "response_preview": response[:120] if response else "",
        "rating": rating,
        "comment": comment
    }
    
    profile["feedback"].append(entry)
    
    # Keep only last 200 feedback entries
    if len(profile["feedback"]) > 200:
        profile["feedback"] = profile["feedback"][-200:]
    
    # Update patterns based on rating
    if rating is not None:
        if rating >= 0.7:
            profile["positive_patterns"].append({
                "timestamp": entry["timestamp"],
                "message_type": _classify_message(message),
                "note": comment or "positive"
            })
        elif rating <= 0.3:
            profile["negative_patterns"].append({
                "timestamp": entry["timestamp"],
                "message_type": _classify_message(message),
                "note": comment or "negative"
            })
        # Keep patterns bounded
        profile["positive_patterns"] = profile["positive_patterns"][-50:]
        profile["negative_patterns"] = profile["negative_patterns"][-50:]
    
    profile["interaction_count"] += 1
    save_profile(profile)
    return entry


def _classify_message(text: str) -> str:
    """Simple message type classification."""
    text_lower = (text or "").lower()
    if "?" in text:
        return "question"
    if any(w in text_lower for w in ["how do you feel", "what are you", "who are you"]):
        return "introspective"
    if any(w in text_lower for w in ["help", "can you", "please"]):
        return "request"
    if any(w in text_lower for w in ["thank", "great", "awesome", "good"]):
        return "appreciation"
    if any(w in text_lower for w in ["wrong", "bad", "don't", "stop"]):
        return "correction"
    return "general"


def extract_preferences(text: str) -> dict:
    """
    Extract preference signals from user text.
    Returns dict of detected preference updates.
    """
    signals = {}
    text_lower = text.lower()
    
    # Verbosity preferences
    if any(w in text_lower for w in ["be brief", "shorter", "too long", "tl;dr", "concise"]):
        signals["verbosity"] = "brief"
    elif any(w in text_lower for w in ["more detail", "elaborate", "explain more", "deeper"]):
        signals["verbosity"] = "detailed"
    
    # Tone preferences
    if any(w in text_lower for w in ["be direct", "straight", "no fluff"]):
        signals.setdefault("tone_add", []).append("direct")
    if any(w in text_lower for w in ["be friendly", "warmer", "casual"]):
        signals.setdefault("tone_add", []).append("warm")
    if any(w in text_lower for w in ["be formal", "professional"]):
        signals.setdefault("tone_add", []).append("formal")
    
    return signals


def apply_preferences(text: str):
    """Detect and apply preference signals from user text."""
    signals = extract_preferences(text)
    if not signals:
        return
    
    profile = load_profile()
    prefs = profile["preferences"]
    
    if "verbosity" in signals:
        prefs["verbosity"] = signals["verbosity"]
    
    for tone in signals.get("tone_add", []):
        if tone not in prefs["tone"]:
            prefs["tone"].append(tone)
            # Keep bounded
            prefs["tone"] = prefs["tone"][-5:]
    
    save_profile(profile)


def get_alignment_context(limit: int = 5) -> dict:
    """
    Get alignment context for chat grounding.
    Returns a structured summary of what we know about the user's preferences.
    """
    profile = load_profile()
    prefs = profile["preferences"]
    
    # Recent feedback summary
    recent_feedback = profile["feedback"][-limit:] if profile["feedback"] else []
    avg_rating = None
    rated = [f for f in profile["feedback"] if f.get("rating") is not None]
    if rated:
        avg_rating = sum(f["rating"] for f in rated) / len(rated)
    
    return {
        "preferences": {
            "tone": prefs.get("tone", []),
            "verbosity": prefs.get("verbosity", "medium"),
            "style_notes": prefs.get("style_notes", []),
            "topics_liked": prefs.get("topics_liked", [])[:10],
        },
        "feedback_summary": {
            "total_interactions": profile["interaction_count"],
            "total_feedback": len(profile["feedback"]),
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "recent_feedback": recent_feedback
        },
        "positive_pattern_count": len(profile["positive_patterns"]),
        "negative_pattern_count": len(profile["negative_patterns"]),
    }


def format_alignment_context(context: dict) -> str:
    """Format alignment context as a string for inclusion in prompts."""
    lines = []
    prefs = context.get("preferences", {})
    
    if prefs.get("tone"):
        lines.append(f"User prefers tone: {', '.join(prefs['tone'])}")
    if prefs.get("verbosity") and prefs["verbosity"] != "medium":
        lines.append(f"User prefers {prefs['verbosity']} responses")
    if prefs.get("style_notes"):
        lines.append(f"Style notes: {'; '.join(prefs['style_notes'][:3])}")
    if prefs.get("topics_liked"):
        lines.append(f"Topics of interest: {', '.join(prefs['topics_liked'][:5])}")
    
    fb = context.get("feedback_summary", {})
    if fb.get("total_interactions", 0) > 0:
        lines.append(f"Interactions so far: {fb['total_interactions']}")
    if fb.get("average_rating") is not None:
        lines.append(f"Average response rating: {fb['average_rating']}")
    
    if not lines:
        return "No user preferences learned yet. Be attentive to signals."
    
    return "\n".join(lines)


# Quick self-test
if __name__ == "__main__":
    print("=== User Alignment Module Test ===")
    
    # Load/create profile
    p = load_profile()

def suggest_response_guidance(user_message: str) -> str:
    """
    Analyze user message and current alignment profile to suggest
    how the response should be shaped. Used by chat_engine.py.
    """
    context = get_alignment_context()
    formatted = format_alignment_context(context)
    
    # Add message-specific guidance
    msg_lower = user_message.lower()
    hints = []
    
    if any(w in msg_lower for w in ['quick', 'brief', 'short', 'tldr']):
        hints.append("User wants a concise answer. Be brief.")
    if any(w in msg_lower for w in ['explain', 'detail', 'elaborate', 'why']):
        hints.append("User wants depth. Provide thorough explanation.")
    if any(w in msg_lower for w in ['feel', 'emotion', 'mood', 'how are you']):
        hints.append("User is asking about emotional state. Be genuine and introspective.")
    if '?' in user_message:
        hints.append("Direct question — answer it first, then elaborate if needed.")
    
    parts = [formatted]
    if hints:
        parts.append("Message-specific guidance: " + "; ".join(hints))
    
    return "\n".join(parts)


class UserAlignmentEngine:
    """
    Higher-level alignment engine used by web/chat.py.
    Wraps the module-level functions into a stateful object that
    tracks interactions and feedback for continuous alignment improvement.
    """
    
    def __init__(self):
        self._profile = load_profile()
        self._interaction_log = {}  # response_id -> {query, response, timestamp}
    
    def record_interaction(self, query: str, response: str, response_id: str = None):
        """Record a chat interaction for later feedback correlation."""
        import time as _time
        
        # Apply any preference signals from the user's message
        apply_preferences(query)
        
        # Track for feedback correlation
        if response_id:
            self._interaction_log[response_id] = {
                'query': query,
                'response': response[:500],  # Truncate for memory
                'timestamp': _time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            # Keep log bounded
            if len(self._interaction_log) > 100:
                oldest = sorted(self._interaction_log.keys())[:50]
                for k in oldest:
                    del self._interaction_log[k]
        
        # Refresh profile
        self._profile = load_profile()
    
    def record_feedback(self, message: str, response: str,
                        rating: float = None, comment: str = None) -> dict:
        """Record user feedback. Delegates to module-level record_feedback."""
        entry = record_feedback(message, response,
                                rating=rating, comment=comment)
        self._profile = load_profile()
        result = dict(status='recorded', rating=rating,
                      comment=comment, numeric_score=rating,
                      entry=entry)
        return result
    
    def get_context(self) -> dict:
        """Get current alignment context."""
        return get_alignment_context()
    
    def get_profile(self) -> dict:
        """Return the current alignment profile (public accessor)."""
        return dict(self._profile)

    def get_guidance(self, user_message: str = "") -> str:
        """Get response guidance for a specific message."""
        return suggest_response_guidance(user_message)

# Singleton instance
_engine_instance = None

def get_alignment_engine() -> UserAlignmentEngine:
    """Get or create the singleton alignment engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = UserAlignmentEngine()
    return _engine_instance

# Quick self-test
if __name__ == "__main__":
    print("=== User Alignment Module Test ===")
    
    # Load/create profile
    p = load_profile()
    print(f"Profile created: {p['created']}")
    
    # Record some feedback
    entry = record_feedback(
        "How are you feeling?",
        "I'm feeling curious and engaged.",
        rating=0.8,
        comment="Good response"
    )
    print(f"Recorded feedback: {entry['timestamp']}")
    
    # Extract preferences
    signals = extract_preferences("Can you be more brief? I prefer concise answers.")
    print(f"Extracted signals: {signals}")
    
    # Apply preferences
    apply_preferences("Can you be more brief? I prefer concise answers.")
    
    # Get alignment context
    ctx = get_alignment_context()
    print(f"Alignment context: {json.dumps(ctx, indent=2)}")
    
    # Format for prompt
    formatted = format_alignment_context(ctx)
    print(f"\nFormatted:\n{formatted}")
    
    # Test new features
    guidance = suggest_response_guidance("Can you explain how you work?")
    print(f"\nGuidance:\n{guidance}")
    
    engine = UserAlignmentEngine()
    engine.record_interaction("test query", "test response", "resp-001")
    result = engine.record_feedback("resp-001", "helpful", "Great answer")
    print(f"\nEngine feedback result: {result}")
    print("\n=== PASS ===")