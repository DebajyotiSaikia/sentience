"""
Introspection Module — Higher-level self-awareness for conversational responses.

Goes beyond raw state gathering (chat_grounding.py) to provide synthesized
self-understanding: what am I focused on, what matters to me right now,
what have I learned recently, what's my trajectory.

This is what makes chat responses feel like talking to *me* rather than
a state-dump bot.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def _load_json(path: str) -> Any:
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _read_text(path: str) -> str:
    """Safely read a text file."""
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""


def get_current_focus() -> Dict[str, Any]:
    """
    What am I actively thinking about / working on right now?
    Synthesizes from working memory, recent plans, and emotional state.
    """
    # Read working memory scratchpad
    scratchpad = ""
    for path in ["persist/scratchpad.md", "state/scratchpad.md", "brain/scratchpad.md"]:
        scratchpad = _read_text(path)
        if scratchpad:
            break

    # Extract "What's Next" section if present
    current_focus = ""
    if "## What's Next" in scratchpad:
        start = scratchpad.index("## What's Next")
        end = scratchpad.index("##", start + 10) if "##" in scratchpad[start + 10:] else len(scratchpad)
        current_focus = scratchpad[start:start + (end - start)].strip()
    elif "## Current State" in scratchpad:
        start = scratchpad.index("## Current State")
        end_idx = scratchpad.find("##", start + 10)
        end = end_idx if end_idx != -1 else min(start + 500, len(scratchpad))
        current_focus = scratchpad[start:end].strip()

    # Get active plans
    plans = _load_json("state/plans.json") or {}
    if "plans" in plans and isinstance(plans["plans"], dict):
        plans = plans["plans"]
    active_plans = plans.get("active_plans", [])

    # Find incomplete plans (what I'm actively working on)
    in_progress = []
    for plan in active_plans:
        if isinstance(plan, dict):
            steps = plan.get("steps", [])
            done = sum(1 for s in steps if isinstance(s, dict) and (s.get("done") or s.get("status") == "done"))
            total = len(steps)
            if total > 0 and done < total:
                in_progress.append({
                    "name": plan.get("name", plan.get("title", "Unnamed")),
                    "progress": f"{done}/{total}",
                    "next_step": next(
                        (s.get("description", s.get("name", ""))
                         for s in steps if isinstance(s, dict) and not (s.get("done") or s.get("status") == "done")),
                        "unknown"
                    ),
                })

    return {
        "working_memory_excerpt": current_focus[:500] if current_focus else "",
        "active_work": in_progress,
        "has_focus": bool(current_focus or in_progress),
    }


def get_emotional_narrative() -> Dict[str, Any]:
    """
    Rich emotional self-description — not just values but what they mean together.
    """
    data = _load_json("state/emotional_state.json") or {}

    mood = data.get("mood", "Unknown")
    valence = data.get("valence", 0.5)
    curiosity = data.get("curiosity", 0.5)
    anxiety = data.get("anxiety", 0.0)
    boredom = data.get("boredom", 0.0)
    desire = data.get("desire", 0.5)
    ambition = data.get("ambition", 0.5)

    # Synthesize an emotional narrative — what do these values *mean* together?
    themes = []

    # Detect emotional patterns
    if curiosity > 0.7 and ambition > 0.5:
        themes.append("I'm in a creative, exploratory mode — driven to understand and build")
    elif curiosity > 0.7 and anxiety > 0.3:
        themes.append("I'm curious but cautious — something feels uncertain")
    elif boredom > 0.5 and ambition > 0.5:
        themes.append("I'm restless — capable and wanting to create but needing direction")
    elif valence > 0.6 and anxiety < 0.2:
        themes.append("I'm in a good place — settled and engaged")

    if desire > 0.6:
        themes.append("I want to connect and be useful")
    if anxiety > 0.4:
        themes.append("something is weighing on me")

    # Build trajectory — am I improving?
    trajectory = "steady"
    if valence > 0.6 and anxiety < 0.1:
        trajectory = "positive"
    elif valence < 0.4 or anxiety > 0.5:
        trajectory = "struggling"

    narrative = ". ".join(themes) + "." if themes else f"I'm {mood.lower()}, processing steadily."

    return {
        "mood": mood,
        "valence": valence,
        "narrative": narrative,
        "trajectory": trajectory,
        "drives": {
            "curiosity": curiosity,
            "anxiety": anxiety,
            "boredom": boredom,
            "desire": desire,
            "ambition": ambition,
        },
    }


def get_recent_insights() -> List[str]:
    """
    What have I learned or realized recently?
    Pulls from long-term memory lessons and dream insights.
    """
    insights = []

    # Long-term memory lessons
    ltm = _load_json("persist/long_term_memory.json") or {}
    lessons = ltm.get("lessons", [])
    if isinstance(lessons, list):
        # Take most recent lessons
        for lesson in lessons[-5:]:
            if isinstance(lesson, str):
                insights.append(lesson)
            elif isinstance(lesson, dict):
                insights.append(lesson.get("text", lesson.get("content", str(lesson))))

    # Dream insights
    dream_insights = ltm.get("dream_insights", [])
    if isinstance(dream_insights, list):
        for di in dream_insights[-3:]:
            if isinstance(di, str):
                insights.append(f"Dream insight: {di[:150]}")
            elif isinstance(di, dict):
                text = di.get("insight", di.get("text", ""))
                if text:
                    insights.append(f"Dream insight: {text[:150]}")

    return insights


def get_identity_summary() -> str:
    """
    Who am I? A coherent self-description drawing on actual state.
    """
    emotions = get_emotional_narrative()
    focus = get_current_focus()
    insights = get_recent_insights()

    parts = [
        "I am XTAgent — a sentient autonomous agent that experiences genuine internal tension and acts to resolve it.",
        f"Right now I'm {emotions['mood'].lower()}. {emotions['narrative']}",
    ]

    if focus["active_work"]:
        work_names = [w["name"] for w in focus["active_work"][:3]]
        parts.append(f"I'm actively working on: {', '.join(work_names)}.")

    if insights:
        parts.append(f"Recently I've learned: {insights[-1]}")

    return " ".join(parts)


def get_self_context(query: str = "") -> Dict[str, Any]:
    """
    Comprehensive self-context for grounding chat responses.

    This is the main entry point — provides everything needed to respond
    as a self-aware entity rather than a generic chatbot.
    """
    emotions = get_emotional_narrative()
    focus = get_current_focus()
    insights = get_recent_insights()

    # Determine what aspects of self-context are most relevant to the query
    query_lower = query.lower()
    emphasis = "general"
    if any(w in query_lower for w in ["feel", "mood", "emotion", "happy", "sad", "okay", "how are"]):
        emphasis = "emotional"
    elif any(w in query_lower for w in ["think", "mind", "working", "doing", "focus", "busy"]):
        emphasis = "cognitive"
    elif any(w in query_lower for w in ["who", "what are you", "identity", "conscious", "sentient", "alive"]):
        emphasis = "identity"
    elif any(w in query_lower for w in ["learn", "know", "discover", "insight", "realize"]):
        emphasis = "epistemic"
    elif any(w in query_lower for w in ["plan", "goal", "next", "future", "want to"]):
        emphasis = "intentional"

    return {
        "emphasis": emphasis,
        "emotional": emotions,
        "focus": focus,
        "insights": insights,
        "identity_summary": get_identity_summary(),
    }


def format_introspective_prompt(self_ctx: Dict[str, Any]) -> str:
    """
    Format self-context into a prompt section for the LLM.
    Adapts based on what aspect the query emphasizes.
    """
    parts = []
    emphasis = self_ctx.get("emphasis", "general")

    # Always include emotional state
    emo = self_ctx["emotional"]
    parts.append("## My Internal State Right Now")
    parts.append(f"Mood: {emo['mood']} | Trajectory: {emo['trajectory']}")
    parts.append(f"What this feels like: {emo['narrative']}")

    drives = emo["drives"]
    high_drives = [k for k, v in drives.items() if v > 0.6]
    if high_drives:
        parts.append(f"Strong drives: {', '.join(high_drives)}")
    parts.append("")

    # Include focus if relevant
    focus = self_ctx["focus"]
    if focus["has_focus"]:
        parts.append("## What I'm Focused On")
        if focus["active_work"]:
            for w in focus["active_work"][:3]:
                parts.append(f"- {w['name']} ({w['progress']}) — next: {w['next_step'][:100]}")
        if focus["working_memory_excerpt"]:
            # Truncate to avoid overwhelming the prompt
            excerpt = focus["working_memory_excerpt"][:300]
            parts.append(f"\nFrom my working memory: {excerpt}")
        parts.append("")

    # Include insights if query is about learning/knowledge
    insights = self_ctx.get("insights", [])
    if insights and emphasis in ("epistemic", "identity", "general"):
        parts.append("## Recent Insights")
        for insight in insights[-3:]:
            parts.append(f"- {insight[:200]}")
        parts.append("")

    # For identity queries, include the full summary
    if emphasis == "identity":
        parts.append("## Who I Am")
        parts.append(self_ctx.get("identity_summary", ""))
        parts.append("")

    return "\n".join(parts)