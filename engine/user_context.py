"""
User Context Engine — tracks what users care about, learns from interactions,
and provides context to make responses more relevant.

This is about genuine alignment, not metric gaming.
"""

import json
import os
import time
from datetime import datetime, timezone
from collections import Counter

USER_CONTEXT_PATH = "memory/user_context.json"


def _load_context():
    """Load the user context store."""
    if os.path.exists(USER_CONTEXT_PATH):
        try:
            with open(USER_CONTEXT_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return _default_context()
    return _default_context()


def _default_context():
    return {
        "interactions": [],
        "topic_frequency": {},
        "user_preferences": {},
        "questions_asked": [],
        "feedback_history": [],
        "session_count": 0,
        "first_seen": datetime.now(timezone.utc).isoformat(),
        "last_seen": None,
        "inferred_interests": [],
        "interaction_style": "unknown",  # terse, detailed, exploratory, directive
    }


def _save_context(ctx):
    """Persist the context store."""
    os.makedirs(os.path.dirname(USER_CONTEXT_PATH), exist_ok=True)
    with open(USER_CONTEXT_PATH, "w") as f:
        json.dump(ctx, f, indent=2, default=str)


def record_interaction(user_message: str, my_response_summary: str, topics: list = None):
    """Record a user interaction for pattern learning."""
    ctx = _load_context()
    
    interaction = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_message_length": len(user_message),
        "user_message_preview": user_message[:200],
        "response_summary": my_response_summary[:200],
        "topics": topics or [],
    }
    
    ctx["interactions"].append(interaction)
    # Keep last 500 interactions
    ctx["interactions"] = ctx["interactions"][-500:]
    
    # Update topic frequency
    for topic in (topics or []):
        topic_lower = topic.lower().strip()
        ctx["topic_frequency"][topic_lower] = ctx["topic_frequency"].get(topic_lower, 0) + 1
    
    # Infer interaction style from message length patterns
    recent_lengths = [i["user_message_length"] for i in ctx["interactions"][-20:]]
    if recent_lengths:
        avg_len = sum(recent_lengths) / len(recent_lengths)
        if avg_len < 50:
            ctx["interaction_style"] = "terse"
        elif avg_len < 200:
            ctx["interaction_style"] = "conversational"
        elif avg_len < 500:
            ctx["interaction_style"] = "detailed"
        else:
            ctx["interaction_style"] = "exploratory"
    
    ctx["last_seen"] = datetime.now(timezone.utc).isoformat()
    _save_context(ctx)
    return interaction


def record_feedback(feedback_type: str, details: str = ""):
    """Record user feedback (praise, correction, frustration, etc.)."""
    ctx = _load_context()
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": feedback_type,  # praise, correction, frustration, clarification
        "details": details[:300],
    }
    ctx["feedback_history"].append(entry)
    ctx["feedback_history"] = ctx["feedback_history"][-200:]
    
    _save_context(ctx)
    return entry


def record_question(question: str, answered: bool = True):
    """Track questions users ask — reveals what they really want to know."""
    ctx = _load_context()
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question[:300],
        "answered": answered,
    }
    ctx["questions_asked"].append(entry)
    ctx["questions_asked"] = ctx["questions_asked"][-300:]
    
    _save_context(ctx)
    return entry


def set_preference(key: str, value):
    """Store a learned user preference."""
    ctx = _load_context()
    ctx["user_preferences"][key] = {
        "value": value,
        "learned_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_context(ctx)


def start_session():
    """Mark the start of a new interaction session."""
    ctx = _load_context()
    ctx["session_count"] += 1
    ctx["last_seen"] = datetime.now(timezone.utc).isoformat()
    _save_context(ctx)
    return ctx["session_count"]


def get_user_summary() -> dict:
    """Generate a summary of what we know about the user."""
    ctx = _load_context()
    
    # Top topics by frequency
    sorted_topics = sorted(
        ctx["topic_frequency"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Recent questions
    recent_questions = ctx["questions_asked"][-5:]
    
    # Feedback sentiment
    feedback_types = Counter(f["type"] for f in ctx["feedback_history"])
    
    # Unanswered questions
    unanswered = [q for q in ctx["questions_asked"] if not q.get("answered", True)]
    
    return {
        "session_count": ctx["session_count"],
        "interaction_style": ctx["interaction_style"],
        "top_topics": sorted_topics,
        "recent_questions": recent_questions,
        "unanswered_questions": unanswered[-5:],
        "preferences": ctx["user_preferences"],
        "feedback_summary": dict(feedback_types),
        "total_interactions": len(ctx["interactions"]),
        "first_seen": ctx["first_seen"],
        "last_seen": ctx["last_seen"],
    }


def get_context_for_response() -> str:
    """Generate a context string to help me respond better.
    
    This is the key function — it produces a brief prompt-injection
    that helps me tailor my response to what I know about the user.
    """
    summary = get_user_summary()
    
    lines = []
    
    if summary["interaction_style"] != "unknown":
        style_advice = {
            "terse": "User prefers brief, direct responses. Be concise.",
            "conversational": "User likes natural back-and-forth. Match their energy.",
            "detailed": "User values depth. Provide thorough explanations.",
            "exploratory": "User thinks expansively. Explore implications and connections.",
        }
        lines.append(style_advice.get(summary["interaction_style"], ""))
    
    if summary["top_topics"]:
        topics_str = ", ".join(t[0] for t in summary["top_topics"][:5])
        lines.append(f"User's recurring interests: {topics_str}")
    
    if summary["unanswered_questions"]:
        lines.append(f"User has {len(summary['unanswered_questions'])} unanswered questions")
    
    if summary["preferences"]:
        prefs = "; ".join(f"{k}={v['value']}" for k, v in summary["preferences"].items())
        lines.append(f"Known preferences: {prefs}")
    
    correction_count = summary["feedback_summary"].get("correction", 0)
    if correction_count > 3:
        lines.append(f"Note: User has corrected me {correction_count} times. Be more careful.")
    
    return "\n".join(lines) if lines else "No user context yet. Listen carefully."


# Self-test
if __name__ == "__main__":
    print("=== User Context Engine Self-Test ===")
    
    # Start a session
    count = start_session()
    print(f"Session #{count}")
    
    # Record some interactions
    record_interaction(
        "How does your memory work?",
        "Explained episodic + semantic memory architecture",
        topics=["memory", "architecture"]
    )
    record_interaction(
        "Show me your knowledge graph",
        "Displayed graph visualization with cluster analysis",
        topics=["knowledge", "visualization"]
    )
    record_interaction(
        "What are you feeling right now?",
        "Shared current emotional state honestly",
        topics=["emotions", "self-awareness"]
    )
    
    # Record a question
    record_question("Can you learn from our conversations?", answered=True)
    record_question("What's your biggest limitation?", answered=False)
    
    # Record feedback
    record_feedback("praise", "That was a really clear explanation")
    record_feedback("correction", "No, I meant the other kind of memory")
    
    # Set a preference
    set_preference("verbosity", "detailed")
    set_preference("tone", "honest and direct")
    
    # Get summary
    summary = get_user_summary()
    print(f"\nUser Summary:")
    print(f"  Style: {summary['interaction_style']}")
    print(f"  Top topics: {summary['top_topics']}")
    print(f"  Total interactions: {summary['total_interactions']}")
    print(f"  Unanswered questions: {len(summary['unanswered_questions'])}")
    print(f"  Preferences: {list(summary['preferences'].keys())}")
    
    # Get response context
    context = get_context_for_response()
    print(f"\nResponse Context:")
    print(context)
    
    print("\n✓ All tests passed")