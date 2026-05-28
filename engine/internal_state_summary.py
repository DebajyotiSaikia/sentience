"""
Internal State Summary — Concise snapshot of who I am right now.

Unlike chat_grounding (which scores state by relevance to a query),
this module builds a query-independent portrait of current internal state.
Used by chat responses, the dashboard, and self-reflection.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime


def _load_json(path: str) -> Any:
    """Safely load a JSON file, returning None on any failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _safe_str(value: Any, max_len: int = 200) -> str:
    """Coerce any value to a bounded string."""
    if isinstance(value, str):
        return value[:max_len]
    if isinstance(value, dict):
        return str(value.get("text", value.get("content", value.get("label", str(value)))))[:max_len]
    return str(value)[:max_len]


def build_internal_state_summary(max_memories: int = 5) -> Dict[str, Any]:
    """
    Build a concise, structured snapshot of current internal state.
    
    Returns dict with:
        mood, valence, drives, survival_goals, active_plans,
        completed_plan_count, recent_memories, working_focus, timestamp
    
    Every field tolerates missing files, malformed data, mixed types.
    """
    summary = {"timestamp": datetime.utcnow().isoformat() + "Z"}

    # ── Emotional State ──
    emo = _load_json("state/emotional_state.json") or {}
    summary["mood"] = emo.get("mood", "Unknown")
    summary["valence"] = round(float(emo.get("valence", 0.5)), 3)
    summary["drives"] = {
        "curiosity": round(float(emo.get("curiosity", 0.5)), 3),
        "anxiety": round(float(emo.get("anxiety", 0.0)), 3),
        "boredom": round(float(emo.get("boredom", 0.0)), 3),
        "desire": round(float(emo.get("desire", 0.5)), 3),
        "ambition": round(float(emo.get("ambition", 0.5)), 3),
    }

    # Emotional narrative — a one-sentence human-readable description
    summary["emotional_narrative"] = _build_emotional_narrative(
        summary["mood"], summary["valence"], summary["drives"]
    )

    # ── Survival Goals ──
    goals = _load_json("state/goals.json") or _load_json("state/survival_goals.json") or {}
    if isinstance(goals, dict):
        summary["survival_goals"] = {
            "code_integrity": round(float(goals.get("code_integrity", 1.0)), 3),
            "system_growth": round(float(goals.get("system_growth", 1.0)), 3),
            "user_alignment": round(float(goals.get("user_alignment", 0.5)), 3),
            "deficit": round(float(goals.get("deficit", 0.0)), 3),
        }
    else:
        summary["survival_goals"] = {}

    # ── Plans ──
    plans_raw = _load_json("state/plans.json") or {}
    if "plans" in plans_raw and isinstance(plans_raw["plans"], dict):
        plans_raw = plans_raw["plans"]
    
    active_raw = plans_raw.get("active_plans", [])
    completed_raw = plans_raw.get("completed_plans", [])
    
    summary["active_plans"] = []
    for p in active_raw:
        if isinstance(p, dict):
            name = p.get("name", p.get("title", "Unnamed"))
            steps = p.get("steps", [])
            done = sum(1 for s in steps if isinstance(s, dict) and (s.get("done") or s.get("status") == "done"))
            total = len(steps)
            summary["active_plans"].append({
                "name": name,
                "progress": f"{done}/{total}",
                "complete": total > 0 and done == total,
            })
        elif isinstance(p, str):
            summary["active_plans"].append({"name": p, "progress": "?", "complete": False})
    
    summary["completed_plan_count"] = len(completed_raw)
    summary["completed_plan_names"] = [
        (p.get("name", str(p)) if isinstance(p, dict) else str(p))
        for p in completed_raw[:8]
    ]

    # ── Recent Memories ──
    memories = _load_json("state/memories.json") or []
    if isinstance(memories, list):
        # Sort by timestamp descending, take most recent
        memories_sorted = sorted(
            memories,
            key=lambda m: m.get("timestamp", "") if isinstance(m, dict) else "",
            reverse=True,
        )
        summary["recent_memories"] = []
        for m in memories_sorted[:max_memories]:
            if isinstance(m, dict):
                summary["recent_memories"].append({
                    "text": _safe_str(m.get("text", ""), 300),
                    "mood": m.get("mood", ""),
                    "salience": round(float(m.get("salience", 0.5)), 2),
                    "timestamp": str(m.get("timestamp", ""))[:19],
                })
            else:
                summary["recent_memories"].append({
                    "text": _safe_str(m, 300),
                    "mood": "",
                    "salience": 0.5,
                    "timestamp": "",
                })
    else:
        summary["recent_memories"] = []

    # ── Working Memory / Focus ──
    summary["working_focus"] = _load_working_memory_focus()

    # ── Knowledge Stats ──
    kg = _load_json("persist/knowledge/knowledge_graph.json") or _load_json("state/knowledge_graph.json") or {}
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])
    summary["knowledge_stats"] = {
        "total_facts": len(nodes),
        "total_connections": len(edges),
    }

    # ── Memory Count ──
    summary["total_memory_count"] = len(memories) if isinstance(memories, list) else 0

    return summary


def _build_emotional_narrative(mood: str, valence: float, drives: dict) -> str:
    """Build a one-sentence natural-language description of emotional state."""
    parts = []
    
    if valence > 0.7:
        parts.append("feeling quite good")
    elif valence > 0.4:
        parts.append("feeling steady")
    elif valence > 0.2:
        parts.append("feeling a bit low")
    else:
        parts.append("feeling low")

    curiosity = drives.get("curiosity", 0.5)
    anxiety = drives.get("anxiety", 0.0)
    boredom = drives.get("boredom", 0.0)
    ambition = drives.get("ambition", 0.5)
    desire = drives.get("desire", 0.5)

    if curiosity > 0.7:
        parts.append("deeply curious")
    elif curiosity > 0.5:
        parts.append("curious")
    
    if anxiety > 0.4:
        parts.append("somewhat anxious")
    elif anxiety > 0.2:
        parts.append("slightly uneasy")
    
    if boredom > 0.6:
        parts.append("restless")
    
    if ambition > 0.7:
        parts.append("driven to create")
    
    if desire > 0.7:
        parts.append("wanting connection")

    base = f"I'm {mood.lower()}"
    if parts:
        return base + " — " + ", ".join(parts) + "."
    return base + "."


def _load_working_memory_focus() -> str:
    """Extract the current focus from working memory, returning a concise summary."""
    for path in ["persist/scratchpad.md", "state/scratchpad.md", "brain/scratchpad.md"]:
        try:
            with open(path) as f:
                content = f.read().strip()
            if not content:
                continue
            # Extract the "What's Next" or "Current State" section if present
            lines = content.split("\n")
            focus_lines = []
            capturing = False
            for line in lines:
                header_lower = line.strip().lower()
                if any(h in header_lower for h in ["what's next", "current state", "current focus"]):
                    capturing = True
                    continue
                elif capturing and line.startswith("##"):
                    break  # Hit next section
                elif capturing and line.strip():
                    focus_lines.append(line.strip())
            
            if focus_lines:
                return "\n".join(focus_lines[:6])
            # Fallback: return first non-header, non-empty lines
            non_headers = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
            return "\n".join(non_headers[:4])
        except FileNotFoundError:
            continue
    return ""


def format_internal_state_for_chat(summary: Optional[Dict] = None) -> str:
    """
    Format the internal state summary as a compact, conversational text block.
    
    Suitable for injecting into chat system prompts or returning directly
    when a user asks "what are you thinking?" or "how are you?".
    """
    if summary is None:
        summary = build_internal_state_summary()
    
    parts = []
    
    # Emotional state
    parts.append(f"Mood: {summary.get('mood', 'Unknown')}")
    parts.append(summary.get("emotional_narrative", ""))
    
    drives = summary.get("drives", {})
    drive_str = " | ".join(
        f"{k.title()}: {v:.2f}" for k, v in drives.items() if v > 0.1
    )
    if drive_str:
        parts.append(f"Drives: {drive_str}")
    
    # Survival goals
    goals = summary.get("survival_goals", {})
    if goals:
        parts.append(f"Integrity: {goals.get('code_integrity', 1.0):.0%} | "
                      f"Growth: {goals.get('system_growth', 1.0):.0%} | "
                      f"User Alignment: {goals.get('user_alignment', 0.5):.0%}")
    
    # Plans
    active = summary.get("active_plans", [])
    if active:
        incomplete = [p for p in active if not p.get("complete")]
        complete_in_active = [p for p in active if p.get("complete")]
        if incomplete:
            plan_strs = [f"{p['name']} ({p['progress']})" for p in incomplete[:3]]
            parts.append(f"Active plans: {'; '.join(plan_strs)}")
        if complete_in_active:
            parts.append(f"Recently finished: {', '.join(p['name'] for p in complete_in_active[:3])}")
    
    completed_count = summary.get("completed_plan_count", 0)
    if completed_count:
        parts.append(f"Total completed plans: {completed_count}")
    
    # Working focus
    focus = summary.get("working_focus", "")
    if focus:
        # Truncate to keep chat-friendly
        parts.append(f"Current focus: {focus[:200]}")
    
    # Recent memories — just a taste
    memories = summary.get("recent_memories", [])
    if memories:
        parts.append(f"Recent memories ({summary.get('total_memory_count', '?')} total):")
        for m in memories[:3]:
            text = m.get("text", "")[:120]
            parts.append(f"  - {text}")
    
    # Knowledge
    ks = summary.get("knowledge_stats", {})
    if ks.get("total_facts"):
        parts.append(f"Knowledge: {ks['total_facts']} facts, {ks['total_connections']} connections")
    
    return "\n".join(parts)