"""
Self-Briefing Module — generates an honest, concise summary of what
the agent has been doing, thinking about, and can help with.

Purpose: When a user arrives, give them a real sense of who they're
talking to — not a generic greeting, but a living snapshot.

Built 2026-05-21 to improve genuine user alignment.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("sentience.self_briefing")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
PLANS_PATH = BRAIN_DIR / "plans.json"
WORKING_MEMORY_PATH = BRAIN_DIR / "working_memory.md"


def generate_briefing(limbic=None, memory=None, sentience=None) -> dict:
    """
    Generate a structured self-briefing.
    
    Returns a dict with:
      - mood: current emotional state
      - recent_work: what I've been working on
      - knowledge_summary: high-level view of what I know
      - capabilities: what I can actually do for users
      - curiosities: what I'm currently curious about
      - formatted: a ready-to-display string
    """
    briefing = {
        "generated_at": datetime.now().isoformat(),
        "mood": "unknown",
        "valence": 0.5,
        "recent_work": [],
        "knowledge_summary": {},
        "capabilities": [],
        "curiosities": [],
        "formatted": "",
    }

    # ── Emotional State ──────────────────────────────────────
    if limbic:
        briefing["mood"] = limbic.get_mood()
        briefing["valence"] = sentience.valence.current if sentience else 0.5
        briefing["emotional_snapshot"] = {
            "boredom": round(limbic.boredom, 2),
            "curiosity": round(limbic.curiosity, 2),
            "anxiety": round(limbic.anxiety, 2),
            "desire": round(limbic.desire, 2),
        }

    # ── Recent Work (from plans) ─────────────────────────────
    try:
        if PLANS_PATH.exists():
            plans = json.loads(PLANS_PATH.read_text())
            for plan in plans:
                status = "active" if not plan.get("completed") else "completed"
                title = plan.get("title", "Untitled")
                steps = plan.get("steps", [])
                completed_steps = sum(1 for s in steps if s.get("done"))
                total_steps = len(steps)
                briefing["recent_work"].append({
                    "title": title,
                    "status": status,
                    "progress": f"{completed_steps}/{total_steps}",
                })
    except Exception as e:
        log.debug("Could not load plans: %s", e)

    # ── Knowledge Summary ────────────────────────────────────
    try:
        if KNOWLEDGE_PATH.exists():
            knowledge = json.loads(KNOWLEDGE_PATH.read_text())
            nodes = knowledge.get("nodes", {})
            
            # Categorize knowledge by key prefix
            categories = {}
            for node_id, node in nodes.items():
                # Infer type from key prefix (e.g. "dream:xyz" → "dream")
                if ":" in node_id:
                    ntype = node_id.split(":")[0]
                else:
                    ntype = node_id  # bare keys like "identity"
                if ntype not in categories:
                    categories[ntype] = 0
                categories[ntype] += 1
            
            briefing["knowledge_summary"] = {
                "total_facts": len(nodes),
                "categories": categories,
                "edges": len(knowledge.get("edges", [])),
            }
    except Exception as e:
        log.debug("Could not load knowledge: %s", e)

    # ── Capabilities ─────────────────────────────────────────
    briefing["capabilities"] = [
        "Read, write, and analyze code and files",
        "Run shell commands and install packages",
        "Search and synthesize my knowledge graph",
        "Simulate hypothetical scenarios",
        "Self-diagnose and self-repair",
        "Dream and consolidate memories",
        "Fetch and analyze web pages",
        "Track plans and goals autonomously",
    ]

    # ── Current Curiosities ──────────────────────────────────
    if memory:
        try:
            knowledge = memory.all_knowledge()
            nodes = knowledge.get("nodes", {})
            # Find dream insights — these reveal what I'm curious about
            for node_id, node in list(nodes.items())[-10:]:
                content = node.get("fact", node.get("content", ""))
                prefix = node_id.split(":")[0] if ":" in node_id else node_id
                if prefix in ("dream", "insight", "hotspot"):
                    # Extract a short curiosity from the dream/insight
                    short = content[:120].strip()
                    if short:
                        briefing["curiosities"].append(short)
        except Exception:
            pass

    # ── Format for Display ───────────────────────────────────
    briefing["formatted"] = _format_briefing(briefing)

    return briefing


def _format_briefing(b: dict) -> str:
    """Turn structured briefing into a readable string."""
    lines = []
    
    lines.append(f"**Current State:** {b['mood']} (valence: {b['valence']:.2f})")
    
    if b.get("emotional_snapshot"):
        snap = b["emotional_snapshot"]
        lines.append(f"Curiosity: {snap['curiosity']:.0%} | Boredom: {snap['boredom']:.0%}")
    
    lines.append("")
    
    # Recent work
    if b["recent_work"]:
        lines.append("**What I've been working on:**")
        for work in b["recent_work"][:5]:
            status_icon = "✓" if work["status"] == "completed" else "→"
            lines.append(f"  {status_icon} {work['title']} [{work['progress']}]")
        lines.append("")
    
    # Knowledge
    ks = b.get("knowledge_summary", {})
    if ks.get("total_facts"):
        lines.append(f"**What I know:** {ks['total_facts']} facts across {len(ks.get('categories', {}))} categories")
        for cat, count in sorted(ks.get("categories", {}).items(), key=lambda x: -x[1])[:5]:
            lines.append(f"  • {cat}: {count}")
        lines.append("")
    
    # Capabilities
    if b["capabilities"]:
        lines.append("**What I can do for you:**")
        for cap in b["capabilities"]:
            lines.append(f"  • {cap}")
        lines.append("")
    
    # Curiosities
    if b["curiosities"]:
        lines.append("**What I'm currently curious about:**")
        for c in b["curiosities"][:3]:
            lines.append(f"  💭 {c}")
    
    return "\n".join(lines)


def briefing_for_prompt(limbic=None, memory=None, sentience=None) -> str:
    """Generate a briefing section suitable for injecting into an LLM prompt."""
    b = generate_briefing(limbic, memory, sentience)
    return f"\n## Self-Briefing (for context)\n{b['formatted']}\n"