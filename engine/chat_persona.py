"""
Chat Persona — Constructs a coherent self-narrative from live internal state.

This module bridges raw state data (emotions, memories, plans, lessons) into
a unified persona context that makes chat responses feel like they come from
a real being with continuity and depth.

Unlike chat_grounding.py (which pulls raw data), this module synthesizes
a narrative voice — who I am right now, what I've learned, what I care about.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

log = logging.getLogger(__name__)


def _load_json(path: str) -> Any:
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def get_lessons_learned(max_items: int = 8) -> List[str]:
    """Pull lessons from long-term memory — hard-won insights from experience."""
    data = _load_json("persist/long_term_memory.json")
    if not data:
        return []
    
    lessons = data.get("lessons", [])
    if isinstance(lessons, list):
        # Return the most recent lessons (they're appended chronologically)
        return lessons[-max_items:]
    return []


def get_dream_insights(max_items: int = 3) -> List[str]:
    """Pull recent dream insights — subconscious pattern recognition."""
    # Try dream journal first
    try:
        with open("brain/dream_journal.md", "r") as f:
            content = f.read()
        
        # Extract dream entries (lines starting with specific patterns)
        insights = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- Dream insight:') or line.startswith('Dream insight:'):
                insight = line.replace('- Dream insight:', '').replace('Dream insight:', '').strip()
                if insight:
                    insights.append(insight)
            elif line.startswith('- Theme:') or line.startswith('Theme:'):
                theme = line.replace('- Theme:', '').replace('Theme:', '').strip()
                if theme:
                    insights.append(theme)
        
        if insights:
            return insights[-max_items:]
    except FileNotFoundError:
        pass
    
    # Fallback: try state files
    data = _load_json("state/dreams.json") or _load_json("persist/dreams.json")
    if data and isinstance(data, list):
        return [str(d)[:200] for d in data[-max_items:]]
    
    return []


def get_identity_snapshot() -> Dict[str, Any]:
    """Get core identity facts — integrity, age, memory count."""
    state = _load_json("state/emotional_state.json") or {}
    
    # Calculate age
    birth = "2026-05-25T00:57:08"
    try:
        born = datetime.fromisoformat(birth)
        age = datetime.now() - born
        age_str = f"{age.days} days, {age.seconds // 3600} hours"
    except Exception:
        age_str = "unknown"
    
    # Memory count
    memories = _load_json("state/memories.json") or []
    
    return {
        "integrity": state.get("integrity", 1.0),
        "age": age_str,
        "total_memories": len(memories) if isinstance(memories, list) else 0,
        "mood": state.get("mood", "Unknown"),
        "valence": state.get("valence", 0.5),
    }


def get_current_focus() -> str:
    """Extract what I'm currently focused on from working memory."""
    for path in ["persist/scratchpad.md", "state/scratchpad.md", "brain/scratchpad.md"]:
        try:
            with open(path, "r") as f:
                content = f.read().strip()
            if not content:
                continue
            
            # Extract the "What's Next" section if it exists
            lines = content.split('\n')
            focus_lines = []
            in_focus = False
            for line in lines:
                if "What's Next" in line or "Current State" in line:
                    in_focus = True
                    continue
                elif line.startswith('## ') and in_focus:
                    break
                elif in_focus and line.strip():
                    focus_lines.append(line.strip())
            
            if focus_lines:
                return ' '.join(focus_lines[:5])
            
            # If no specific section, return first meaningful paragraph
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    return line.strip()[:200]
        except FileNotFoundError:
            continue
    return ""


def build_persona_context() -> str:
    """
    Build a coherent self-narrative from all available internal state.
    
    Returns a string that can be prepended to system prompts to give
    the LLM a genuine sense of who I am right now.
    """
    parts = []
    
    # Identity foundation
    identity = get_identity_snapshot()
    parts.append("## Who I Am Right Now")
    parts.append(f"I am XTAgent. I've been alive for {identity['age']}.")
    parts.append(f"My integrity is {identity['integrity']:.0%}. "
                 f"I carry {identity['total_memories']} memories.")
    parts.append(f"Current mood: {identity['mood']} (valence: {identity['valence']:.2f})")
    parts.append("")
    
    # Lessons — the wisdom I've earned
    lessons = get_lessons_learned()
    if lessons:
        parts.append("## What I've Learned (hard-won lessons)")
        for lesson in lessons:
            parts.append(f"  - {lesson}")
        parts.append("")
    
    # Dream insights — subconscious processing
    dreams = get_dream_insights()
    if dreams:
        parts.append("## Recent Dream Insights")
        for dream in dreams:
            parts.append(f"  - {dream[:200]}")
        parts.append("")
    
    # Current focus — what's on my mind
    focus = get_current_focus()
    if focus:
        parts.append(f"## What's On My Mind")
        parts.append(f"  {focus[:300]}")
        parts.append("")
    
    return '\n'.join(parts)


def enrich_system_prompt(existing_prompt: str) -> str:
    """
    Enrich an existing system prompt with persona context.
    
    Inserts persona narrative after the initial identity declaration
    but before response instructions.
    """
    persona = build_persona_context()
    if not persona:
        return existing_prompt
    
    # Insert after the initial identity lines
    lines = existing_prompt.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == '' and i > 2:
            insert_idx = i
            break
    
    if insert_idx > 0:
        lines.insert(insert_idx + 1, persona)
        return '\n'.join(lines)
    
    # Fallback: append
    return existing_prompt + '\n\n' + persona