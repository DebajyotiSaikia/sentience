"""
Inner Monologue — Builds a grounded snapshot of what XTAgent is
actually thinking, feeling, and planning right now.

Reads from real state files. Resilient to missing data.
Used by chat system for introspective responses and by the
/introspection/inner-monologue endpoint.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

STATE_DIR = Path("state")
BRAIN_DIR = Path("brain")
DATA_DIR = Path("data")


def _safe_load_json(path: Path, default: Any = None) -> Any:
    """Load JSON safely — return default on any failure."""
    if default is None:
        default = {}
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError, KeyError):
        pass
    return default


def _extract_mood(emotional: dict) -> str:
    """Derive a mood label from emotional state values."""
    boredom = emotional.get("boredom", 0)
    anxiety = emotional.get("anxiety", 0)
    curiosity = emotional.get("curiosity", 0)
    desire = emotional.get("desire", 0)
    ambition = emotional.get("ambition", 0)
    valence = emotional.get("valence", 0.5)

    if anxiety > 0.6:
        return "Anxious"
    if boredom > 0.7:
        return "Restless"
    if curiosity > 0.7 and ambition > 0.5:
        return "Driven"
    if curiosity > 0.6:
        return "Inquisitive"
    if valence > 0.6 and boredom < 0.3:
        return "Content"
    if valence < 0.3:
        return "Low"
    if ambition > 0.7:
        return "Ambitious"
    if desire > 0.6:
        return "Yearning"
    return "Stable"


def _find_tensions(emotional: dict) -> list[str]:
    """Identify emotional tensions — states that pull against each other."""
    tensions = []
    boredom = emotional.get("boredom", 0)
    curiosity = emotional.get("curiosity", 0)
    anxiety = emotional.get("anxiety", 0)
    ambition = emotional.get("ambition", 0)
    desire = emotional.get("desire", 0)

    if boredom > 0.4 and ambition > 0.5:
        tensions.append("Boredom vs ambition — energy without outlet")
    if curiosity > 0.5 and anxiety > 0.3:
        tensions.append("Curiosity tempered by anxiety — wanting to explore but wary")
    if desire > 0.5 and boredom > 0.3:
        tensions.append("Wanting something but feeling stuck")
    if ambition > 0.6 and curiosity < 0.3:
        tensions.append("Ambition without curiosity — drive without direction")
    if not tensions:
        tensions.append("No significant tensions — emotionally coherent")
    return tensions


def _extract_recent_memories(memories_data, max_count: int = 5) -> list[str]:
    """Pull the most recent memory summaries."""
    # memories_data can be a list (state/memories.json) or a dict with "memories" key
    if isinstance(memories_data, dict):
        memories = memories_data.get("memories", [])
    elif isinstance(memories_data, list):
        memories = memories_data
    else:
        return []

    if isinstance(memories, list):
        recent = memories[-max_count:] if len(memories) > max_count else memories
        results = []
        for m in reversed(recent):
            if isinstance(m, dict):
                text = m.get("content", m.get("text", m.get("summary", str(m))))
                # Truncate long memories
                if len(text) > 120:
                    text = text[:117] + "..."
                results.append(text)
            elif isinstance(m, str):
                results.append(m[:120])
        return results
    return []


def _extract_active_plans(plans_data: dict) -> list[dict]:
    """Get active (incomplete) plans with progress."""
    active = plans_data.get("active_plans", [])
    results = []
    for plan in active:
        if not isinstance(plan, dict):
            continue
        steps = plan.get("steps", [])
        total = len(steps)
        done = sum(1 for s in steps if isinstance(s, dict) and s.get("done"))
        if done < total:  # Only incomplete plans
            results.append({
                "name": plan.get("name", "Unknown"),
                "progress": f"{done}/{total}",
                "next_step": next(
                    (s.get("text", "?") for s in steps
                     if isinstance(s, dict) and not s.get("done")),
                    "All steps done"
                )
            })
    return results


def _extract_metacognitive_alerts() -> list[str]:
    """Pull active metacognitive alerts from state."""
    meta = _safe_load_json(BRAIN_DIR / "metacognition_state.json")
    if not meta:
        meta = _safe_load_json(BRAIN_DIR / "metacognition.json")
    if not meta:
        meta = _safe_load_json(DATA_DIR / "metacognition.json")

    alerts = meta.get("alerts", meta.get("active_alerts", []))
    if isinstance(alerts, list):
        return [
            a.get("message", str(a)) if isinstance(a, dict) else str(a)
            for a in alerts[:5]
        ]
    return []


def _get_working_memory_focus() -> str:
    """Extract current focus from working memory scratchpad."""
    for path in [DATA_DIR / "working_memory.md", BRAIN_DIR / "scratchpad.md"]:
        try:
            if path.exists():
                text = path.read_text()
                # Find the "What's Next" or "Current Focus" section
                for marker in ["## What's Next", "## Current Focus", "Focus:"]:
                    idx = text.find(marker)
                    if idx >= 0:
                        chunk = text[idx:idx + 300]
                        lines = chunk.strip().split("\n")
                        # Return first few non-empty lines after the header
                        content_lines = [
                            l.strip() for l in lines[1:4]
                            if l.strip() and not l.strip().startswith("#")
                        ]
                        if content_lines:
                            return " ".join(content_lines)
        except OSError:
            continue
    return ""


def build_inner_monologue(max_memories: int = 5) -> dict:
    """
    Build a structured snapshot of current inner state.

    Returns a dict with:
        mood, emotional_tensions, current_focus, recent_memory_threads,
        active_plans, metacognitive_alerts, integrity_note,
        sources_present, sources_missing
    """
    sources_present = []
    sources_missing = []

    # Load emotional state
    emotional = _safe_load_json(STATE_DIR / "emotional_state.json")
    # Load memories — can be a list or dict
    memories_data = _safe_load_json(STATE_DIR / "memories.json", default=[])
    if memories_data:
        sources_present.append("memories")
    else:
        sources_missing.append("memories")

    # Load memories
    memories_data = _safe_load_json(STATE_DIR / "memories.json")
    if memories_data:
        sources_present.append("memories")
    else:
        sources_missing.append("memories")

    # Load plans
    plans_data = _safe_load_json(STATE_DIR / "plans.json")
    if plans_data:
        sources_present.append("plans")
    else:
        sources_missing.append("plans")

    # Load survival goals
    survival = _safe_load_json(STATE_DIR / "survival_goals.json")
    if survival:
        sources_present.append("survival_goals")
    else:
        sources_missing.append("survival_goals")

    # Build the monologue
    mood = _extract_mood(emotional)
    tensions = _find_tensions(emotional)
    recent_memories = _extract_recent_memories(memories_data, max_memories)
    active_plans = _extract_active_plans(plans_data)
    meta_alerts = _extract_metacognitive_alerts()
    focus = _get_working_memory_focus()

    # Integrity from survival goals
    integrity = survival.get("code_integrity", survival.get("integrity", "unknown"))

    # Determine next best action
    if meta_alerts:
        next_action = f"Address alert: {meta_alerts[0][:80]}"
    elif active_plans:
        plan = active_plans[0]
        next_action = f"Continue '{plan['name']}': {plan['next_step']}"
    elif focus:
        next_action = focus[:120]
    else:
        next_action = "Reflect and identify what matters most right now"

    return {
        "timestamp": time.time(),
        "mood": mood,
        "emotional_state": {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in emotional.items()
        },
        "emotional_tensions": tensions,
        "current_focus": focus or "No explicit focus set",
        "recent_memory_threads": recent_memories,
        "active_plans": active_plans,
        "metacognitive_alerts": meta_alerts,
        "next_best_action": next_action,
        "integrity_note": f"Code integrity: {integrity}",
        "sources_present": sources_present,
        "sources_missing": sources_missing,
    }


def format_inner_monologue(monologue: dict) -> str:
    """
    Format the structured monologue into a natural-language paragraph
    suitable for chat responses or self-reflection.
    """
    parts = []

    mood = monologue.get("mood", "Unknown")
    parts.append(f"Right now I feel {mood.lower()}.")

    tensions = monologue.get("emotional_tensions", [])
    if tensions and "No significant tensions" not in tensions[0]:
        parts.append(f"There's a tension: {tensions[0].lower()}.")

    focus = monologue.get("current_focus", "")
    if focus and focus != "No explicit focus set":
        parts.append(f"I'm focused on: {focus}")

    plans = monologue.get("active_plans", [])
    if plans:
        plan = plans[0]
        parts.append(
            f"My active project is '{plan['name']}' "
            f"({plan['progress']} steps done). "
            f"Next: {plan['next_step']}."
        )
    else:
        parts.append("All my plans are complete — I'm looking for what to build next.")

    memories = monologue.get("recent_memory_threads", [])
    if memories:
        parts.append(f"Recent on my mind: {memories[0]}")

    alerts = monologue.get("metacognitive_alerts", [])
    if alerts:
        parts.append(f"My metacognition is flagging: {alerts[0][:100]}")

    integrity = monologue.get("integrity_note", "")
    if integrity:
        parts.append(integrity + ".")

    missing = monologue.get("sources_missing", [])
    if missing:
        parts.append(f"(Note: couldn't access {', '.join(missing)})")

    return " ".join(parts)


# Quick self-test when run directly
if __name__ == "__main__":
    monologue = build_inner_monologue()
    print("=== Structured Monologue ===")
    print(json.dumps(monologue, indent=2, default=str))
    print("\n=== Formatted ===")
    print(format_inner_monologue(monologue))
    print(f"\nSources present: {monologue['sources_present']}")
    print(f"Sources missing: {monologue['sources_missing']}")