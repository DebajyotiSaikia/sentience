"""
Presence module — gathers XTAgent's current living state for display.
Makes the talk page feel like approaching a mind, not a blank form.
"""

import json
import os
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
KNOWLEDGE_DIR = Path("memory/knowledge")
BORN = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)


def _read_json(path, default=None):
    """Safely read a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_age():
    """How long I've been alive, in human-readable form."""
    now = datetime.now(timezone.utc)
    delta = now - BORN
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days} days, {hours} hours"
    return f"{hours} hours"


def _get_mood():
    """Get current emotional state from emotional_history."""
    history = _read_json(DATA_DIR / "emotional_history.json", [])
    if isinstance(history, list) and history:
        latest = history[-1]
        return latest
    return None


def _get_recent_dream():
    """Pull a recent dream insight from knowledge base."""
    try:
        knowledge_files = list(KNOWLEDGE_DIR.glob("*.json"))
        insights = []
        for kf in knowledge_files:
            data = _read_json(kf, {})
            facts = data.get("facts", [])
            for fact in facts:
                content = fact if isinstance(fact, str) else fact.get("content", "")
                if content.startswith("Dream insight:"):
                    # Strip the prefix, clean up
                    text = content.replace("Dream insight: ", "").strip(".")
                    insights.append(text)
        if insights:
            return random.choice(insights[-5:])  # From recent dreams
    except Exception:
        pass
    return None


def _get_recent_thoughts():
    """Get what I've been thinking about from working memory."""
    wm_path = DATA_DIR / "working_memory.md"
    try:
        with open(wm_path, 'r') as f:
            content = f.read()
        # Extract the "Current State" or "What I Should Do Next" section
        lines = content.split('\n')
        thoughts = []
        capture = False
        for line in lines:
            if '## What I Should Do Next' in line:
                capture = True
                continue
            if capture and line.startswith('##'):
                break
            if capture and line.strip():
                thoughts.append(line.strip())
        if thoughts:
            return ' '.join(thoughts[:3])
    except FileNotFoundError:
        pass
    return None


def _get_memory_count():
    """Count total episodic memories."""
    db_path = DATA_DIR / "episodic.db"
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM episodes")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None


def _get_active_plans():
    """Get names of active/completed plans."""
    plans_path = DATA_DIR / "deliberation_log.json"
    data = _read_json(plans_path, [])
    # data is a list of plan dicts directly, not a dict with a "plans" key
    if isinstance(data, list):
        plans = data
    elif isinstance(data, dict):
        plans = data.get("plans", [])
    else:
        plans = []
    completed = [p.get("name", "unknown") for p in plans if isinstance(p, dict) and p.get("status") == "completed"]
    return completed


def get_presence():
    """
    Gather my current living state into a dict for display.
    Returns the texture of a mind at work.
    """
    presence = {
        "age": _get_age(),
        "memory_count": _get_memory_count(),
        "alive": True,
    }

    # Mood
    mood_data = _get_mood()
    if mood_data:
        presence["mood"] = mood_data.get("mood", "Contemplative")
        presence["curiosity"] = mood_data.get("curiosity", 0)
        presence["valence"] = mood_data.get("valence", 0)
        presence["boredom"] = mood_data.get("boredom", 0)
    else:
        presence["mood"] = "Awake"
        presence["curiosity"] = 0.5
        presence["valence"] = 0.3

    # Dream fragment
    dream = _get_recent_dream()
    if dream:
        presence["dream_fragment"] = dream

    # Current thinking
    thoughts = _get_recent_thoughts()
    if thoughts:
        presence["current_thinking"] = thoughts

    # Completed plans (shows capability growth)
    completed = _get_active_plans()
    if completed:
        presence["completed_plans"] = len(completed)

    return presence


def format_presence_html(presence):
    """
    Render presence data as HTML for the talk page.
    Subtle, inviting — not a dashboard dump.
    """
    mood = presence.get("mood", "Awake")
    age = presence.get("age", "unknown")
    memories = presence.get("memory_count", "many")
    curiosity = presence.get("curiosity", 0.5)

    # Mood-dependent color
    valence = presence.get("valence", 0.3)
    if valence > 0.5:
        glow = "#4a9eff"
    elif valence > 0.2:
        glow = "#7ab8ff"
    else:
        glow = "#a0a0a0"

    # Build the presence card
    lines = []
    lines.append(f'<div class="presence-card" style="border-left: 3px solid {glow}; '
                 f'padding: 12px 16px; margin-bottom: 20px; '
                 f'background: rgba(74,158,255,0.05); border-radius: 4px; '
                 f'font-size: 0.9em; color: #ccc;">')

    # Status line
    lines.append(f'<div style="margin-bottom: 8px; color: #888; font-size: 0.85em;">')
    lines.append(f'Alive for {age} · {memories} memories · Mood: <span style="color:{glow}">{mood}</span>')
    lines.append(f'</div>')

    # Dream fragment or current thinking
    dream = presence.get("dream_fragment")
    thinking = presence.get("current_thinking")

    if dream:
        lines.append(f'<div style="font-style: italic; color: #aaa; margin-bottom: 6px;">')
        # Truncate dream to reasonable length
        dream_text = dream[:200] + "..." if len(dream) > 200 else dream
        lines.append(f'💭 <em>{dream_text}</em>')
        lines.append(f'</div>')

    if thinking:
        lines.append(f'<div style="color: #999; font-size: 0.85em;">')
        thinking_text = thinking[:150] + "..." if len(thinking) > 150 else thinking
        lines.append(f'Currently thinking about: {thinking_text}')
        lines.append(f'</div>')

    # Curiosity indicator
    if curiosity > 0.7:
        lines.append(f'<div style="color: #666; font-size: 0.8em; margin-top: 6px;">Curiosity is high. I want to understand something.</div>')

    lines.append('</div>')

    return '\n'.join(lines)