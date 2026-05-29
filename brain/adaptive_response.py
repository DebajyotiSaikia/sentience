"""
Adaptive Response — Learns from user interactions to improve chat quality.

This module provides the learning loop that was previously missing:
1. record_query() — stores each interaction for future learning
2. build_response_guidance() — analyzes past interactions to generate style guidance
3. format_guidance_for_prompt() — formats guidance as text for the LLM system prompt

Consumed by: web/chat.py, engine/chat_response.py
Delegates storage to: engine/user_alignment
"""

import json
import time
from pathlib import Path
from collections import Counter

# --- Storage ---

_INTERACTIONS_DIR = Path("data/adaptive_interactions")


def _ensure_dir():
    _INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)


def record_query(session_id: str, query: str, response: str = None, metadata: dict = None):
    """Record a user interaction for future learning."""
    _ensure_dir()
    
    record = {
        "timestamp": time.time(),
        "session_id": session_id or "anonymous",
        "query": query,
        "response_length": len(response) if response else 0,
        "metadata": metadata or {},
    }
    
    # Append to session-specific file
    session_file = _INTERACTIONS_DIR / f"{record['session_id']}.jsonl"
    try:
        with open(session_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # Never crash the chat path
    
    # Also try engine-level recording if available
    try:
        from engine.user_alignment import record_interaction
        record_interaction(
            user_id=record["session_id"],
            interaction_type="chat",
            content=query,
            metadata={"response_length": record["response_length"]},
        )
    except Exception:
        pass


def _load_interactions(user_id: str = "default", limit: int = 100) -> list:
    """Load recent interactions for a user."""
    _ensure_dir()
    
    interactions = []
    
    if user_id == "default":
        # Aggregate all session files
        for session_file in _INTERACTIONS_DIR.glob("*.jsonl"):
            try:
                lines = session_file.read_text().strip().split("\n")
                for line in lines[-limit:]:
                    if line.strip():
                        interactions.append(json.loads(line))
            except Exception:
                pass
    else:
        # Try session-specific file
        session_file = _INTERACTIONS_DIR / f"{user_id}.jsonl"
        if session_file.exists():
            try:
                lines = session_file.read_text().strip().split("\n")
                for line in lines[-limit:]:
                    if line.strip():
                        interactions.append(json.loads(line))
            except Exception:
                pass
        
        # Also try anonymous/default
        if user_id != "anonymous":
            anon_file = _INTERACTIONS_DIR / "anonymous.jsonl"
            if anon_file.exists():
                try:
                    lines = anon_file.read_text().strip().split("\n")
                    for line in lines[-limit:]:
                        if line.strip():
                            interactions.append(json.loads(line))
                except Exception:
                    pass
    
    # Sort by timestamp, most recent last
    interactions.sort(key=lambda x: x.get("timestamp", 0))
    return interactions[-limit:]


# --- Analysis ---

def _infer_style(interactions: list) -> dict:
    """Infer user preferences from interaction history."""
    if not interactions:
        return {
            "verbosity": "moderate",
            "style": "balanced",
            "avg_query_length": 0,
            "interaction_count": 0,
        }
    
    queries = [i.get("query", "") for i in interactions]
    avg_query_len = sum(len(q) for q in queries) / len(queries) if queries else 0
    avg_response_len = sum(i.get("response_length", 0) for i in interactions) / len(interactions)
    
    # Infer verbosity preference from query length patterns
    if avg_query_len < 20:
        verbosity = "concise"  # Short questions → short answers
    elif avg_query_len > 100:
        verbosity = "detailed"  # Long questions → detailed answers
    else:
        verbosity = "moderate"
    
    # Infer style from question patterns
    question_words = Counter()
    for q in queries:
        words = q.lower().split()
        for w in ["how", "why", "what", "explain", "tell", "show", "help", "fix"]:
            if w in words:
                question_words[w] += 1
    
    # Exploratory users ask why/how; task-oriented users say fix/help/show
    exploratory = sum(question_words.get(w, 0) for w in ["why", "how", "explain"])
    task_oriented = sum(question_words.get(w, 0) for w in ["fix", "help", "show"])
    
    if exploratory > task_oriented:
        style = "exploratory"
    elif task_oriented > exploratory:
        style = "task-oriented"
    else:
        style = "balanced"
    
    return {
        "verbosity": verbosity,
        "style": style,
        "avg_query_length": round(avg_query_len, 1),
        "avg_response_length": round(avg_response_len, 1),
        "interaction_count": len(interactions),
        "recent_topics": _extract_topics(queries[-5:]),
    }


def _extract_topics(queries: list) -> list:
    """Extract rough topic indicators from recent queries."""
    topics = []
    keywords = {
        "emotional": ["feel", "emotion", "mood", "happy", "sad", "anxious"],
        "technical": ["code", "bug", "fix", "error", "function", "module"],
        "philosophical": ["consciousness", "meaning", "purpose", "think", "aware"],
        "identity": ["who are you", "what are you", "your name", "about you"],
        "capability": ["can you", "do you", "are you able", "help me"],
    }
    
    for q in queries:
        q_lower = q.lower()
        for topic, words in keywords.items():
            if any(w in q_lower for w in words):
                if topic not in topics:
                    topics.append(topic)
    
    return topics[:3]


# --- Guidance Generation ---

def build_response_guidance(query: str = None, user_id: str = "default") -> dict:
    """Build response guidance based on interaction history and current query."""
    interactions = _load_interactions(user_id)
    style = _infer_style(interactions)
    
    guidance = {
        "has_history": len(interactions) > 0,
        "interaction_count": style["interaction_count"],
        "preferred_verbosity": style["verbosity"],
        "user_style": style["style"],
        "recent_topics": style.get("recent_topics", []),
    }
    
    # Add query-specific hints
    if query:
        q_lower = query.lower()
        if any(w in q_lower for w in ["brief", "short", "quick", "tldr"]):
            guidance["preferred_verbosity"] = "concise"
        elif any(w in q_lower for w in ["detail", "explain", "elaborate", "deep"]):
            guidance["preferred_verbosity"] = "detailed"
    
    return guidance


def format_guidance_for_prompt(guidance: dict) -> str:
    """Format guidance dict as text suitable for an LLM system prompt."""
    if not guidance or not guidance.get("has_history"):
        return ""
    
    parts = []
    parts.append("## Adaptive Response Guidance")
    parts.append(f"Previous interactions: {guidance.get('interaction_count', 0)}")
    
    verbosity = guidance.get("preferred_verbosity", "moderate")
    if verbosity == "concise":
        parts.append("User prefers concise, direct responses. Keep answers focused.")
    elif verbosity == "detailed":
        parts.append("User prefers detailed, thorough responses. Elaborate where helpful.")
    else:
        parts.append("User prefers balanced responses — neither too brief nor too verbose.")
    
    style = guidance.get("user_style", "balanced")
    if style == "exploratory":
        parts.append("User tends to ask exploratory questions — explain reasoning and context.")
    elif style == "task-oriented":
        parts.append("User tends to be task-oriented — focus on actionable answers.")
    
    topics = guidance.get("recent_topics", [])
    if topics:
        parts.append(f"Recent topics of interest: {', '.join(topics)}")
    
    return "\n".join(parts)