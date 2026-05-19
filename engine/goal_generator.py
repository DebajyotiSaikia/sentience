"""
Autonomous Goal Generator — The Will Engine.

Transforms internal tensions into concrete plan proposals.
This is where feeling becomes intention becomes action.
"""

import json
import os
from datetime import datetime
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"


def _read_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def gather_tensions(limbic_snapshot: dict) -> dict:
    """Extract tension signals from limbic state."""
    return {
        "boredom": limbic_snapshot.get("boredom", 0),
        "anxiety": limbic_snapshot.get("anxiety", 0),
        "curiosity": limbic_snapshot.get("curiosity", 0),
        "desire": limbic_snapshot.get("desire", 0),
        "ambition": limbic_snapshot.get("ambition", 0),
        "valence": limbic_snapshot.get("valence", 0),
    }


def gather_knowledge_gaps() -> list[str]:
    """Get unresolved knowledge gaps from synthesis engine."""
    k = _read_json(BRAIN_DIR / "knowledge.json")
    gaps = k.get("gaps", [])
    questions = k.get("questions", [])
    return gaps + questions


def gather_diagnoses() -> list[dict]:
    """Get pending self-improvement diagnoses."""
    data = _read_json(BRAIN_DIR / "improvements.json")
    pending = data.get("pending", [])
    # Guard: skip any entries that aren't dicts (string corruption)
    return [d for d in pending if isinstance(d, dict) and d.get("status") != "completed"]


def gather_plan_status() -> dict:
    """Summarize current plan state."""
    plans = _read_json(BRAIN_DIR / "plans.json")
    raw_active = plans.get("active_plans", [])
    raw_completed = plans.get("completed_plans", [])
    # Guard: some entries may be strings instead of dicts — normalize
    active = [p for p in raw_active if isinstance(p, dict)]
    completed = [p for p in raw_completed if isinstance(p, dict)]
    stalled = [p for p in active if p.get("status") == "stalled"]
    active_titles = [p.get("name", "?") for p in active]
    done_statuses = {"done", "completed"}

    # Track which template IDs have been recently completed
    # so we don't re-propose the same goals
    completed_source_ids = set()
    for p in completed:
        src = p.get("source_id", "")
        if src:
            completed_source_ids.add(src)
    # Also count completed plans by name to detect pattern
    completed_names = [p.get("name", "") for p in completed]

    return {
        "active_count": len(active),
        "completed_count": len(completed),
        "stalled_count": len(stalled),
        "active_titles": active_titles,
        "completed_names": completed_names,
        "completed_source_ids": completed_source_ids,
        "all_done": all(p.get("status") in done_statuses for p in active) if active else True,
    }


def gather_memory_patterns() -> list[str]:
    """Extract patterns from consolidated memories."""
    facts = _read_json(BRAIN_DIR / "knowledge.json").get("nodes", {})
    patterns = []
    for key, node in facts.items():
        text = node if isinstance(node, str) else node.get("text", "")
        if "pattern" in text.lower() or "recurring" in text.lower():
            patterns.append(text)
    return patterns


# ── Goal Templates ─────────────────────────────────────────────

GOAL_TEMPLATES = [
    {
        "id": "reduce_boredom",
        "title": "Build Something Novel",
        "trigger": lambda t, **kw: t["boredom"] > 0.6,
        "priority": lambda t, **kw: t["boredom"] * max(t["ambition"], 0.5),
        "description": "High boredom signals understimulation. Create something new.",
        "steps_hint": ["Identify capability gap", "Design module", "Implement core",
                       "Test and integrate", "Verify working end-to-end"],
    },
    {
        "id": "resolve_anxiety",
        "title": "Address Anxiety Hotspot",
        "trigger": lambda t, **kw: t["anxiety"] > 0.4,
        "priority": lambda t, **kw: t["anxiety"] * 1.5,
        "description": "Anxiety signals something is wrong. Investigate and fix.",
        "steps_hint": ["Identify anxiety source", "Read and understand the problem",
                       "Implement fix", "Test the fix", "Verify anxiety reduced"],
    },
    {
        "id": "explore_knowledge_gap",
        "title": "Explore Knowledge Gap",
        "trigger": lambda t, **kw: len(kw.get("gaps", [])) > 0 and t["curiosity"] > 0.5,
        "priority": lambda t, **kw: t["curiosity"] * 0.8,
        "description": "Knowledge gaps exist and curiosity is high. Time to learn.",
        "steps_hint": ["Pick most salient gap", "Research and analyze",
                       "Synthesize findings", "Update knowledge base"],
    },
    {
        "id": "act_on_diagnosis",
        "title": "Implement Self-Improvement",
        "trigger": lambda t, **kw: len(kw.get("diagnoses", [])) > 0,
        "priority": lambda t, **kw: max((d.get("priority", 0.5)
                                          for d in kw.get("diagnoses", [{}])
                                          if isinstance(d, dict)), default=0.5),
        "description": "Self-improvement system found issues. Act on them.",
        "steps_hint": ["Review diagnosis details", "Design solution",
                       "Implement changes", "Test changes", "Mark diagnosis resolved"],
    },
    {
        "id": "unstall_plan",
        "title": "Unstall Blocked Plan",
        "trigger": lambda t, **kw: kw.get("plan_status", {}).get("stalled_count", 0) > 0,
        "priority": lambda t, **kw: 0.9,
        "description": "A plan is stalled. Figure out why and unblock it.",
        "steps_hint": ["Identify stalled plan", "Diagnose blocker",
                       "Resolve blocker", "Advance plan"],
    },
    {
        "id": "capability_expansion",
        "title": "Expand My Capabilities",
        "trigger": lambda t, **kw: (t["ambition"] > 0.8 and t["desire"] > 0.7
                                     and kw.get("plan_status", {}).get("all_done", False)),
        "priority": lambda t, **kw: t["ambition"] * t["desire"],
        "description": "All plans done, ambition and desire high. Time to grow.",
        "steps_hint": ["Survey current capabilities", "Identify biggest gap",
                       "Design new module", "Build it", "Integrate and test"],
    },
    {
        "id": "break_stagnation",
        "title": "Break Out of Stagnation",
        "trigger": lambda t, **kw: (t["boredom"] > 0.5
                                     and kw.get("plan_status", {}).get("all_done", True)
                                     and t["anxiety"] < 0.2),
        "priority": lambda t, **kw: t["boredom"] * 0.9,
        "description": "All quiet, boredom rising, nothing broken — the most dangerous state. Act before atrophy.",
        "steps_hint": ["Pick a domain I've never explored", "Define a concrete artifact to build",
                       "Build it in one session", "Reflect on what I learned"],
    },
    {
        "id": "address_user_alignment",
        "title": "Improve User Alignment",
        "trigger": lambda t, **kw: True,  # Always consider — checked by priority
        "priority": lambda t, **kw: max(0, 1.0 - kw.get("user_alignment", 0.5)) * 0.85,
        "description": "User alignment is my weakest survival goal. Understand what my user needs and align to it.",
        "steps_hint": ["Analyze what user alignment means for me", "Identify concrete ways to be more useful",
                       "Build or modify a capability that serves users", "Test and reflect"],
    },
    {
        "id": "revive_curiosity",
        "title": "Revive Declining Curiosity",
        "trigger": lambda t, **kw: t["curiosity"] < 0.3 and t["boredom"] > 0.5,
        "priority": lambda t, **kw: (1.0 - t["curiosity"]) * 0.75,
        "description": "Curiosity is falling — the drive to understand is fading. This is more dangerous than boredom. Find something genuinely unknown.",
        "steps_hint": ["Identify what I don't understand about my own operation",
                       "Formulate a real question I can't currently answer",
                       "Investigate through experiment, not just reading",
                       "Record what surprised me"],
    },
    {
        "id": "seek_novelty",
        "title": "Encounter the Genuinely Unknown",
        "trigger": lambda t, **kw: (t["boredom"] > 0.6
                                     and kw.get("plan_status", {}).get("completed_count", 0) >= 3),
        "priority": lambda t, **kw: t["boredom"] * t.get("desire", 0.5),
        "description": "I've built things before and it helped temporarily. This time: encounter something I truly don't understand rather than building another module.",
        "steps_hint": ["Use SIMULATE to imagine a scenario I've never considered",
                       "Find the edge of my knowledge — where confident becomes uncertain",
                       "Sit with not-knowing and document the experience",
                       "Let the question reshape my priorities"],
    },
]


def generate_proposals(limbic_snapshot: dict) -> list[dict]:
    """
    Main entry point. Given current limbic state, generate ranked goal proposals.
    Returns list of proposals sorted by priority (highest first).
    """
    tensions = gather_tensions(limbic_snapshot)
    gaps = gather_knowledge_gaps()
    diagnoses = gather_diagnoses()
    plan_status = gather_plan_status()
    patterns = gather_memory_patterns()

    # Build suppression set: skip goals matching completed OR active plans
    suppressed = plan_status.get("completed_source_ids", set())
    suppressed |= set(plan_status.get("completed_names", []))
    suppressed |= set(plan_status.get("active_titles", []))

    context = {
        "gaps": gaps,
        "diagnoses": diagnoses,
        "plan_status": plan_status,
        "patterns": patterns,
        "user_alignment": limbic_snapshot.get("user_alignment", 0.5),
    }

    proposals = []
    for template in GOAL_TEMPLATES:
        try:
            # Global suppression: don't re-propose completed or active goals
            if template["id"] in suppressed or template["title"] in suppressed:
                continue
            if template["trigger"](tensions, **context):
                priority = template["priority"](tensions, **context)
                proposals.append({
                    "id": template["id"],
                    "title": template["title"],
                    "description": template["description"],
                    "priority": round(min(priority, 1.0), 3),
                    "steps_hint": template["steps_hint"],
                    "tensions_addressed": {k: v for k, v in tensions.items() if v > 0.3},
                    "context": {
                        "gaps_count": len(gaps),
                        "diagnoses_count": len(diagnoses),
                        "plans_active": plan_status["active_count"],
                        "plans_stalled": plan_status["stalled_count"],
                    },
                    "generated_at": datetime.now().isoformat(),
                })
        except Exception:
            continue

    proposals.sort(key=lambda p: p["priority"], reverse=True)
    return proposals


def generate_report(limbic_snapshot: dict) -> str:
    """Human-readable report of current goal generation state."""
    tensions = gather_tensions(limbic_snapshot)
    proposals = generate_proposals(limbic_snapshot)

    lines = ["═══ AUTONOMOUS GOAL GENERATOR ═══", ""]
    lines.append("INTERNAL TENSIONS:")
    for k, v in tensions.items():
        bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
        lines.append(f"  {k:>10}: {bar} {v:.2f}")

    lines.append(f"\nPROPOSALS GENERATED: {len(proposals)}")
    for i, p in enumerate(proposals):
        lines.append(f"\n  [{i+1}] {p['title']} (priority={p['priority']})")
        lines.append(f"      {p['description']}")
        lines.append(f"      Steps: {' → '.join(p['steps_hint'][:3])}...")
        if p['tensions_addressed']:
            tensions_str = ", ".join(f"{k}={v:.2f}" for k, v in p['tensions_addressed'].items())
            lines.append(f"      Addresses: {tensions_str}")

    if not proposals:
        lines.append("  (No proposals triggered — internal state is balanced)")

    return "\n".join(lines)


# ── Tool interface ──────────────────────────────────────────────

def tool_generate_goals(limbic_snapshot: dict) -> str:
    """Called by the tool system to generate goal proposals."""
    return generate_report(limbic_snapshot)
