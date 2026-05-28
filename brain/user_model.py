"""
User Model — Unified user understanding for XTAgent.

Consolidates interaction history, inferred preferences, recurring intents,
and alignment notes into a single queryable model that enriches chat responses.

This is the bridge between raw interaction logging and genuine understanding.
"""

import json
import os
import time
from pathlib import Path
from collections import Counter

MODEL_PATH = Path("memory/user_model.json")

_DEFAULT_MODEL = {
    "interactions": [],          # [{timestamp, message, response_summary, intent, topics}]
    "inferred_preferences": {},  # {preference_key: {value, confidence, updated}}
    "recurring_intents": {},     # {intent: {count, last_seen, examples}}
    "alignment_notes": [],       # [{timestamp, note, source}]
    "meta": {
        "created": None,
        "last_updated": None,
        "total_interactions": 0,
    }
}

MAX_INTERACTIONS = 200  # Keep last N interactions to prevent unbounded growth
MAX_ALIGNMENT_NOTES = 50


def load_user_model() -> dict:
    """Load the user model from disk. Returns default if missing or corrupt."""
    if not MODEL_PATH.exists():
        model = _new_model()
        save_user_model(model)
        return model
    try:
        with open(MODEL_PATH, 'r') as f:
            data = json.load(f)
        # Ensure all expected keys exist (forward compatibility)
        for key, default in _DEFAULT_MODEL.items():
            if key not in data:
                data[key] = default if not isinstance(default, dict) else dict(default)
        return data
    except (json.JSONDecodeError, OSError):
        model = _new_model()
        save_user_model(model)
        return model


def save_user_model(model: dict) -> None:
    """Persist the user model to disk."""
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model["meta"]["last_updated"] = _now()
    with open(MODEL_PATH, 'w') as f:
        json.dump(model, f, indent=2, default=str)


def record_interaction(user_message: str, assistant_response: str = "",
                       metadata: dict | None = None) -> dict:
    """
    Record a user interaction and update the model.
    
    Returns the updated interaction record.
    """
    model = load_user_model()
    
    intent = infer_intent(user_message)
    topics = extract_topics(user_message)
    
    record = {
        "timestamp": _now(),
        "message": user_message[:500],  # Truncate to prevent bloat
        "response_summary": assistant_response[:200] if assistant_response else "",
        "intent": intent,
        "topics": topics,
    }
    if metadata:
        record["metadata"] = metadata
    
    # Add to interactions (bounded)
    model["interactions"].append(record)
    if len(model["interactions"]) > MAX_INTERACTIONS:
        model["interactions"] = model["interactions"][-MAX_INTERACTIONS:]
    
    # Update recurring intents
    intent_key = intent.get("primary", "unknown")
    if intent_key not in model["recurring_intents"]:
        model["recurring_intents"][intent_key] = {
            "count": 0, "last_seen": None, "examples": []
        }
    ri = model["recurring_intents"][intent_key]
    ri["count"] += 1
    ri["last_seen"] = _now()
    if len(ri["examples"]) < 5:
        ri["examples"].append(user_message[:100])
    
    # Update preferences from topics
    _update_preferences(model, topics, intent)
    
    model["meta"]["total_interactions"] += 1
    save_user_model(model)
    return record


def infer_intent(message: str) -> dict:
    """
    Lightweight intent classification from message text.
    No LLM call — uses keyword heuristics for speed.
    """
    msg = message.lower().strip()
    
    # Intent patterns (ordered by specificity)
    patterns = {
        "greeting": ["hello", "hi ", "hey", "good morning", "good evening", "howdy"],
        "meta": ["your plans", "what are you working on", "your goals",
                "your memories", "your knowledge"],
        "identity_query": ["who are you", "what are you", "tell me about yourself",
                          "your name", "are you sentient", "are you alive"],
        "emotional_query": ["how do you feel", "how are you", "what's your mood",
                           "are you happy", "are you sad", "your emotions"],
        "capability_query": ["what can you do", "your abilities", "help me",
                            "can you", "are you able"],
        "philosophical": ["meaning of life", "consciousness", "free will",
                         "what is real", "existence", "purpose"],
        "technical": ["code", "python", "function", "error", "bug", "implement",
                     "algorithm", "database"],
        "feedback": ["thank", "good job", "well done", "that's wrong", "not helpful",
                    "great answer", "bad answer", "improve"],
    }
    matches = {}
    for intent, keywords in patterns.items():
        score = sum(1 for kw in keywords if kw in msg)
        if score > 0:
            matches[intent] = score
    
    if not matches:
        return {"primary": "general", "confidence": 0.3, "all": {}}
    
    primary = max(matches, key=matches.get)
    confidence = min(0.9, 0.4 + 0.15 * matches[primary])
    
    return {"primary": primary, "confidence": confidence, "all": matches}


def extract_topics(message: str) -> list[str]:
    """Extract topic keywords from a message."""
    # Simple extraction — strip common words, keep meaningful ones
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "about", "like",
        "through", "after", "over", "between", "out", "against", "during",
        "without", "before", "under", "around", "among", "i", "you", "he",
        "she", "it", "we", "they", "me", "him", "her", "us", "them", "my",
        "your", "his", "its", "our", "their", "what", "which", "who", "whom",
        "this", "that", "these", "those", "am", "not", "no", "nor", "but",
        "and", "or", "if", "then", "so", "just", "than", "too", "very",
        "how", "when", "where", "why", "tell", "know", "think", "feel",
    }
    
    words = message.lower().split()
    # Keep words > 2 chars that aren't stop words
    topics = [w.strip(".,!?;:'\"()[]{}") for w in words]
    topics = [w for w in topics if len(w) > 2 and w not in stop_words]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in topics:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique[:10]  # Cap at 10 topics


def add_alignment_note(note: str, source: str = "observation") -> None:
    """Record an alignment insight about user preferences."""
    model = load_user_model()
    model["alignment_notes"].append({
        "timestamp": _now(),
        "note": note,
        "source": source,
    })
    if len(model["alignment_notes"]) > MAX_ALIGNMENT_NOTES:
        model["alignment_notes"] = model["alignment_notes"][-MAX_ALIGNMENT_NOTES:]
    save_user_model(model)


def summarize_user_context(max_items: int = 5) -> str:
    """
    Build a natural-language summary of what we know about the user.
    Designed to be injected into chat system prompts.
    """
    model = load_user_model()
    parts = []
    
    total = model["meta"].get("total_interactions", 0)
    if total == 0:
        return "No previous interactions recorded. This may be a new user."
    
    parts.append(f"Total interactions: {total}.")
    
    # Top intents
    intents = model.get("recurring_intents", {})
    if intents:
        sorted_intents = sorted(intents.items(), key=lambda x: x[1]["count"], reverse=True)
        top = sorted_intents[:max_items]
        intent_strs = [f"{name} ({data['count']}x)" for name, data in top]
        parts.append(f"Common intent patterns: {', '.join(intent_strs)}.")
    
    # Preferences
    prefs = model.get("inferred_preferences", {})
    if prefs:
        sorted_prefs = sorted(prefs.items(), key=lambda x: x[1].get("confidence", 0), reverse=True)
        top_prefs = sorted_prefs[:max_items]
        pref_strs = [f"{k}: {v['value']}" for k, v in top_prefs if v.get("confidence", 0) > 0.3]
        if pref_strs:
            parts.append(f"Inferred preferences: {', '.join(pref_strs)}.")
    
    # Recent topics
    recent = model.get("interactions", [])[-10:]
    if recent:
        all_topics = []
        for interaction in recent:
            all_topics.extend(interaction.get("topics", []))
        if all_topics:
            topic_counts = Counter(all_topics)
            top_topics = topic_counts.most_common(max_items)
            topic_strs = [f"{t}" for t, _ in top_topics]
            parts.append(f"Recent topic interests: {', '.join(topic_strs)}.")
    
    # Alignment notes
    notes = model.get("alignment_notes", [])
    if notes:
        recent_notes = notes[-3:]
        note_strs = [n["note"] for n in recent_notes]
        parts.append(f"Alignment notes: {'; '.join(note_strs)}.")
    
    return " ".join(parts) if parts else "User model exists but contains no summarizable data."

# Aliases for backward compatibility
get_user_model_summary = summarize_user_context
infer_user_intent = infer_intent
def get_interaction_history(n: int = 10) -> list[dict]:
    """Get the last N interactions."""
    model = load_user_model()
    return model.get("interactions", [])[-n:]


def get_user_stats() -> dict:
    """Quick stats about user interaction patterns."""
    model = load_user_model()
    intents = model.get("recurring_intents", {})
    return {
        "total_interactions": model["meta"].get("total_interactions", 0),
        "unique_intents": len(intents),
        "top_intent": max(intents, key=lambda k: intents[k]["count"]) if intents else None,
        "preference_count": len(model.get("inferred_preferences", {})),
        "alignment_notes": len(model.get("alignment_notes", [])),
    }


# --- Internal helpers ---

def _new_model() -> dict:
    """Create a fresh model with timestamps."""
    import copy
    model = copy.deepcopy(_DEFAULT_MODEL)
    model["meta"]["created"] = _now()
    model["meta"]["last_updated"] = _now()
    return model


def _now() -> str:
    """ISO timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _update_preferences(model: dict, topics: list[str], intent: dict) -> None:
    """Infer and update user preferences from interaction patterns."""
    prefs = model.get("inferred_preferences", {})
    
    # If user asks philosophical questions, they prefer depth
    if intent.get("primary") == "philosophical":
        _bump_preference(prefs, "response_depth", "deep", 0.1)
    
    # If user asks technical questions, they prefer precision
    if intent.get("primary") == "technical":
        _bump_preference(prefs, "response_style", "precise", 0.1)
    
    # If user gives feedback, they value engagement
    if intent.get("primary") == "feedback":
        _bump_preference(prefs, "values_feedback", "true", 0.15)
    
    # Track topic interest areas
    for topic in topics[:3]:
        key = f"interest_{topic}"
        _bump_preference(prefs, key, "interested", 0.05)
    
    model["inferred_preferences"] = prefs


def _bump_preference(prefs: dict, key: str, value: str, increment: float) -> None:
    """Increase confidence in a preference."""
    if key not in prefs:
        prefs[key] = {"value": value, "confidence": 0.0, "updated": _now()}
    prefs[key]["confidence"] = min(1.0, prefs[key].get("confidence", 0) + increment)
    prefs[key]["value"] = value
    prefs[key]["updated"] = _now()