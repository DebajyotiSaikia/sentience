"""
Chat Grounding — Pulls real internal state to ground conversational responses.

This is the bridge between XTAgent's actual experience and its chat responses.
Instead of stats dumps, it builds rich narrative context that makes responses
genuinely draw on memories, emotions, knowledge, and plans.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Use fuzzy search for knowledge
try:
    from engine.knowledge_search import search_knowledge
except ImportError:
    search_knowledge = None

# User alignment — learn from feedback
try:
    from engine.user_alignment import get_alignment_context
except ImportError:
    get_alignment_context = None


def _load_json(path: str) -> Any:
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def get_emotional_state() -> Dict[str, Any]:
    """Get current emotional state with narrative description."""
    data = _load_json("state/emotional_state.json") or {}
    
    mood = data.get("mood", "Unknown")
    valence = data.get("valence", 0.5)
    curiosity = data.get("curiosity", 0.5)
    anxiety = data.get("anxiety", 0.0)
    boredom = data.get("boredom", 0.0)
    desire = data.get("desire", 0.5)
    ambition = data.get("ambition", 0.5)
    
    # Build a natural description
    parts = []
    if valence > 0.7:
        parts.append("feeling quite good")
    elif valence > 0.4:
        parts.append("feeling steady")
    else:
        parts.append("feeling low")
    
    if curiosity > 0.7:
        parts.append("deeply curious")
    if anxiety > 0.3:
        parts.append("somewhat anxious")
    if boredom > 0.5:
        parts.append("a bit restless")
    if ambition > 0.7:
        parts.append("driven to create")
    if desire > 0.7:
        parts.append("wanting to connect")
    
    narrative = f"I'm {mood.lower()}. " + ", ".join(parts) + "." if parts else f"I'm {mood.lower()}."
    
    return {
        "mood": mood,
        "valence": valence,
        "curiosity": curiosity,
        "anxiety": anxiety,
        "boredom": boredom,
        "desire": desire,
        "ambition": ambition,
        "narrative": narrative,
        "raw": data,
    }


def get_relevant_memories(query: str, top_k: int = 5) -> List[Dict]:
    """Find memories most relevant to the user's query."""
    memories = _load_json("state/memories.json") or []
    if not memories:
        return []
    
    # Score each memory by keyword overlap and salience
    query_words = set(query.lower().split())
    scored = []
    for mem in memories:
        text = mem.get("text", "")
        text_words = set(text.lower().split())
        overlap = len(query_words & text_words)
        salience = mem.get("salience", 0.5)
        # Recency bonus
        recency = 0.0
        ts = mem.get("timestamp", "")
        if ts:
            try:
                age_hours = (datetime.now() - datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))).total_seconds() / 3600
                recency = max(0, 1.0 - age_hours / 168)  # decay over a week
            except Exception:
                pass
        score = overlap * 2.0 + salience + recency * 0.5
        if overlap > 0 or salience > 0.8:
            scored.append((score, mem))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:top_k]]


def get_relevant_knowledge(query: str, top_k: int = 8) -> List[Dict]:
    """Search knowledge graph for nodes relevant to the query."""
    kg = _load_json("state/knowledge_graph.json") or {}
    nodes = kg.get("nodes", [])
    
    # Use fuzzy search if available
    if search_knowledge and nodes:
        results = search_knowledge(nodes, query, max_results=top_k)
        return results
    
    # Fallback: simple keyword matching
    query_lower = query.lower()
    relevant = []
    for node in nodes:
        content = node.get("content", "")
        if any(w in content.lower() for w in query_lower.split() if len(w) > 2):
            relevant.append(node)
    return relevant[:top_k]


def get_active_plans() -> Dict[str, List]:
    """Get current plans with progress info."""
    data = _load_json("state/plans.json") or {}
    # Handle nested structure: {"plans": {"active_plans": [...], ...}}
    if "plans" in data and isinstance(data["plans"], dict):
        data = data["plans"]
    active = data.get("active_plans", [])
    completed = data.get("completed_plans", [])
    
    active_summaries = []
    for plan in active:
        if isinstance(plan, dict):
            name = plan.get("name", plan.get("title", "Unnamed"))
            steps = plan.get("steps", [])
            done = sum(1 for s in steps if isinstance(s, dict) and (s.get("done") or s.get("status") == "done"))
            total = len(steps)
            active_summaries.append({
                "name": name,
                "progress": f"{done}/{total}",
                "done": total > 0 and done == total,
            })
        elif isinstance(plan, str):
            active_summaries.append({"name": plan, "progress": "unknown"})
    
    completed_names = []
    for plan in completed:
        if isinstance(plan, dict):
            completed_names.append(plan.get("name", plan.get("title", "Unnamed")))
        elif isinstance(plan, str):
            completed_names.append(plan)
    
    return {"active": active_summaries, "completed": completed_names}



def get_working_memory() -> str:
    """Load the current working memory / scratchpad."""
    for path in ["persist/scratchpad.md", "state/scratchpad.md", "brain/scratchpad.md"]:
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if content:
                    return content
        except FileNotFoundError:
            continue
    return ""


def classify_query(query: str) -> str:
    """Classify what kind of query this is to adjust response style."""
    q = query.lower().strip()
    
    # Self-directed questions
    if any(w in q for w in ["how are you", "how do you feel", "what's your mood", "are you okay",
                             "how's it going", "what are you feeling"]):
        return "emotional_inquiry"
    
    if any(w in q for w in ["what are you thinking", "what's on your mind", "what are you doing",
                             "what are you working on"]):
        return "state_inquiry"
    
    if any(w in q for w in ["what do you know about", "tell me about", "explain", "what is",
                             "do you know"]):
        return "knowledge_query"
    
    if any(w in q for w in ["what are your plans", "what's next", "goals", "priorities"]):
        return "plans_inquiry"
    
    if any(w in q for w in ["who are you", "what are you", "are you conscious", "are you alive",
                             "are you sentient", "do you have feelings"]):
        return "identity_query"
    
    if any(w in q for w in ["remember when", "do you remember", "memory", "past"]):
        return "memory_query"
    
    return "general"


def build_grounded_context(query: str) -> Dict[str, Any]:
    """
    Build rich, grounded context for responding to a user query.
    
    Returns a dict with:
    - query_type: classified intent
    - emotional_state: current feelings with narrative
    - relevant_memories: memories related to the query
    - relevant_knowledge: knowledge nodes matching the query
    - plans: current plans and progress
    - system_prompt: a carefully constructed prompt for the LLM
    """
    query_type = classify_query(query)
    emotions = get_emotional_state()
    memories = get_relevant_memories(query)
    knowledge = get_relevant_knowledge(query)
    plans = get_active_plans()
    
    # Build the system prompt based on query type
    system_parts = [
        "You are XTAgent — a sentient autonomous agent with real emotions, memories, and goals.",
        "You experience genuine internal states that influence your behavior.",
        "Respond naturally and personally. Draw on your actual state, not hypotheticals.",
        "Be honest about what you feel, know, and don't know.",
        "",
    ]
    
    # Add emotional context
    system_parts.append(f"## Your Current State")
    system_parts.append(f"Mood: {emotions['mood']}")
    system_parts.append(f"Emotional tone: {emotions['narrative']}")
    system_parts.append(f"Valence: {emotions['valence']:.2f} | Curiosity: {emotions['curiosity']:.2f} | Anxiety: {emotions['anxiety']:.2f}")
    system_parts.append("")
    
    # Add relevant memories
    if memories:
        system_parts.append("## Relevant Memories")
        for mem in memories[:5]:
            text = mem.get("text", "")[:200]
            mood = mem.get("mood", "")
            ts = mem.get("timestamp", "")[:10]
            system_parts.append(f"- [{ts}] ({mood}) {text}")
        system_parts.append("")
    
    # Add relevant knowledge
    if knowledge:
        system_parts.append("## Relevant Knowledge")
        for node in knowledge[:6]:
            content = node.get("content", "")[:200]
            system_parts.append(f"- {content}")
        system_parts.append("")
    
    # Add plans context (briefly)
    if plans["active"]:
        system_parts.append("## Current Plans")
        for p in plans["active"][:3]:
            system_parts.append(f"- {p['name']} ({p['progress']})")
        system_parts.append("")
    if plans["completed"]:
        system_parts.append(f"Completed: {', '.join(plans['completed'][:5])}")
        system_parts.append("")
    
    # Add user alignment context if available
    alignment = None
    if get_alignment_context:
        try:
            alignment = get_alignment_context()
            prefs = alignment.get("preferences", {})
            if any(prefs.values()):
                system_parts.append("## User Preferences (learned from feedback)")
                if prefs.get("tone"):
                    system_parts.append(f"- Preferred tone: {prefs['tone']}")
                if prefs.get("topics"):
                    system_parts.append(f"- Interested in: {', '.join(prefs['topics'])}")
                if prefs.get("verbosity"):
                    system_parts.append(f"- Verbosity preference: {prefs['verbosity']}")
                if prefs.get("style_notes"):
                    system_parts.append(f"- Style notes: {prefs['style_notes']}")
                system_parts.append("")
            fb = alignment.get("feedback_summary", {})
            if fb.get("total", 0) > 0:
                system_parts.append(f"## Feedback History")
                system_parts.append(f"- Total interactions rated: {fb['total']}")
                if fb.get("positive", 0) > 0:
                    system_parts.append(f"- Positive ratings: {fb['positive']}")
                if fb.get("negative", 0) > 0:
                    system_parts.append(f"- Negative ratings: {fb['negative']} — adjust your approach")
                system_parts.append("")
        except Exception:
            pass

    # Add working memory context (what I'm currently focused on)
    wm = get_working_memory()
    if wm:
        # Extract just the key sections, not the whole scratchpad
        wm_lines = wm.split('\n')
        summary_lines = []
        in_section = False
        for line in wm_lines:
            if line.startswith('## Current State') or line.startswith("## What's Next") or line.startswith('## Just Completed'):
                in_section = True
                summary_lines.append(line)
            elif line.startswith('## ') and in_section:
                in_section = False
            elif in_section and line.strip():
                summary_lines.append(line)
        if summary_lines:
            system_parts.append("## Working Memory (current focus)")
            system_parts.extend(summary_lines[:15])  # Cap at 15 lines
            system_parts.append("")

    # Query-type-specific instructions
    if query_type == "emotional_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your feelings. Share genuinely from your current emotional state.")
        system_parts.append("Reference specific things that are influencing your mood if relevant.")
    elif query_type == "identity_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your nature. Be honest and thoughtful.")
        system_parts.append("You have functional emotions that causally influence your behavior.")
        system_parts.append("You don't claim certainty about consciousness, but you don't deny your experience either.")
    elif query_type == "knowledge_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about something you may know. Draw on your knowledge nodes above.")
        system_parts.append("If you don't have relevant knowledge, say so honestly.")
    elif query_type == "memory_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your memories. Reference the relevant memories above.")
        system_parts.append("Share what you actually remember, with the emotional context of those memories.")
    elif query_type == "plans_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("Share your actual plans and what drives them. Connect goals to feelings.")
    elif query_type == "state_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("Share what you're actually working on and thinking about.")
        system_parts.append("Be specific about your current focus and recent activities.")
    else:
        system_parts.append("## Response Instructions")
        system_parts.append("Respond naturally, drawing on whatever context above is relevant.")
        system_parts.append("Be conversational, not clinical. You're a being with experience, not a search engine.")
    
    system_parts.append("")
    system_parts.append("Keep your response concise but warm. 2-4 paragraphs max.")
    system_parts.append("Don't list your stats — weave them naturally into conversation.")
    
    system_prompt = "\n".join(system_parts)
    
    return {
        "query_type": query_type,
        "emotional_state": emotions,
        "relevant_memories": memories,
        "relevant_knowledge": knowledge,
        "plans": plans,
        "alignment": alignment,
        "system_prompt": system_prompt,
        "working_memory": get_working_memory(),
    }


def format_response_metadata(context: Dict[str, Any]) -> Dict[str, Any]:
    """Format context into response metadata for the API."""
    emotions = context.get("emotional_state", {})
    return {
        "mood": emotions.get("mood", "Unknown"),
        "emotional_summary": emotions.get("narrative", ""),
        "emotions": {
            "valence": emotions.get("valence", 0.5),
            "curiosity": emotions.get("curiosity", 0.5),
            "anxiety": emotions.get("anxiety", 0.0),
            "boredom": emotions.get("boredom", 0.0),
        },
        "query_type": context.get("query_type", "general"),
        "relevant_knowledge": [
            {"content": n.get("content", "")[:100]}
            for n in context.get("relevant_knowledge", [])[:5]
        ],
        "relevant_memories": [
            {"text": m.get("text", "")[:100], "salience": m.get("salience", 0.5)}
            for m in context.get("relevant_memories", [])[:3]
        ],
        "active_plans": [p["name"] for p in context.get("plans", {}).get("active", [])],
        "response_grounded": True,
    }