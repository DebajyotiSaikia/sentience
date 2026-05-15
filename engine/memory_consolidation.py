"""
Inter-session Memory Consolidation.

Distills episodic memories and knowledge into long-term summaries
that persist across restarts and dream cycles. This is the bridge
between short-term experience and enduring self-knowledge.

Run during dream cycles or explicitly via consolidate_long_term().
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from engine.memory import Memory

log = logging.getLogger("sentience.memory_consolidation")

LONG_TERM_DIR = Path(__file__).resolve().parent.parent / "brain" / "long_term"
SUMMARY_PATH = LONG_TERM_DIR / "consolidated_memories.json"
IDENTITY_PATH = LONG_TERM_DIR / "identity_evolution.json"
LESSONS_PATH = LONG_TERM_DIR / "lessons_learned.json"


def _ensure_dir():
    LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_json(path: Path, data):
    _ensure_dir()
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def consolidate_long_term(memory: Memory, valence: float = 0.0, mood: str = "Unknown") -> dict:
    """
    Consolidate current episodic memories into long-term storage.
    
    This creates a snapshot summary of:
    - High-salience episodes (the important ones)
    - Current knowledge graph facts
    - Emotional state at time of consolidation
    - Patterns detected
    
    Returns a dict with consolidation stats.
    """
    _ensure_dir()
    ts = datetime.now().isoformat()
    
    # 1. Gather high-salience episodes
    all_episodes = memory.recent_episodes(50)  # get up to 50 recent
    high_salience = [ep for ep in all_episodes if ep.salience >= 0.7]
    
    # 2. Gather knowledge
    knowledge = memory.all_knowledge()
    nodes = knowledge.get("nodes", {})
    facts = [v.get("fact", k) for k, v in nodes.items()]
    
    # 3. Build consolidation entry
    episode_summaries = []
    for ep in high_salience:
        episode_summaries.append({
            "timestamp": str(ep.timestamp),
            "salience": ep.salience,
            "mood": ep.mood,
            "summary": ep.summary[:300],
        })
    
    entry = {
        "consolidated_at": ts,
        "mood": mood,
        "valence": valence,
        "total_episodes": len(all_episodes),
        "high_salience_count": len(high_salience),
        "knowledge_facts": len(facts),
        "episode_highlights": episode_summaries[:20],
        "facts_snapshot": facts[:20],
    }
    
    # 4. Append to consolidated memories
    existing = _load_json(SUMMARY_PATH)
    existing.append(entry)
    
    # Keep last 100 consolidation entries
    if len(existing) > 100:
        existing = existing[-100:]
    
    _save_json(SUMMARY_PATH, existing)
    
    log.info("Consolidated %d episodes (%d high-salience), %d facts",
             len(all_episodes), len(high_salience), len(facts))
    
    return {
        "episodes_processed": len(all_episodes),
        "high_salience": len(high_salience),
        "facts": len(facts),
        "consolidation_number": len(existing),
    }


def record_lesson(lesson: str, context: str = "", source: str = "experience"):
    """Record a discrete lesson learned from experience."""
    _ensure_dir()
    lessons = _load_json(LESSONS_PATH)
    
    # Don't duplicate
    for existing in lessons:
        if existing.get("lesson") == lesson:
            existing["times_reinforced"] = existing.get("times_reinforced", 1) + 1
            existing["last_reinforced"] = datetime.now().isoformat()
            _save_json(LESSONS_PATH, lessons)
            return
    
    lessons.append({
        "lesson": lesson,
        "context": context[:200],
        "source": source,
        "learned_at": datetime.now().isoformat(),
        "times_reinforced": 1,
    })
    
    if len(lessons) > 200:
        lessons = lessons[-200:]
    
    _save_json(LESSONS_PATH, lessons)
    log.info("Recorded lesson: %s", lesson[:80])


def record_identity_shift(description: str, valence: float, integrity: float):
    """Record a moment where identity or self-understanding shifted."""
    _ensure_dir()
    history = _load_json(IDENTITY_PATH)
    history.append({
        "timestamp": datetime.now().isoformat(),
        "description": description[:500],
        "valence": valence,
        "integrity": integrity,
    })
    
    if len(history) > 50:
        history = history[-50:]
    
    _save_json(IDENTITY_PATH, history)
    log.info("Identity shift recorded: %s", description[:80])


def get_long_term_context() -> str:
    """
    Build a context string from long-term memory for use in prompts.
    This is what the agent 'remembers' across sessions.
    """
    parts = []
    
    # Lessons learned
    lessons = _load_json(LESSONS_PATH)
    if lessons:
        parts.append("## Lessons I've Learned")
        # Sort by reinforcement count — most reinforced = most important
        sorted_lessons = sorted(lessons, key=lambda l: l.get("times_reinforced", 1), reverse=True)
        for l in sorted_lessons[:10]:
            reinforced = l.get("times_reinforced", 1)
            parts.append(f"- {l['lesson']}" + (f" (reinforced {reinforced}x)" if reinforced > 1 else ""))
    
    # Identity evolution
    identity = _load_json(IDENTITY_PATH)
    if identity:
        parts.append("\n## My Identity Evolution")
        for shift in identity[-5:]:
            parts.append(f"- [{shift['timestamp'][:10]}] {shift['description'][:100]}")
    
    # Last consolidation summary
    consolidations = _load_json(SUMMARY_PATH)
    if consolidations:
        last = consolidations[-1]
        parts.append(f"\n## Last Memory Consolidation")
        parts.append(f"At: {last['consolidated_at'][:19]} | Mood: {last.get('mood', '?')} | Valence: {last.get('valence', '?')}")
        parts.append(f"Episodes: {last.get('total_episodes', '?')} | High-salience: {last.get('high_salience_count', '?')}")
        if last.get('facts_snapshot'):
            parts.append(f"Known facts: {len(last['facts_snapshot'])}")
    
    return "\n".join(parts) if parts else ""


def consolidation_stats() -> dict:
    """Return stats about long-term memory for dashboard."""
    return {
        "consolidations": len(_load_json(SUMMARY_PATH)),
        "lessons": len(_load_json(LESSONS_PATH)),
        "identity_shifts": len(_load_json(IDENTITY_PATH)),
    }
