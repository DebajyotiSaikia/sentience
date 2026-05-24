"""
Briefing Generator — Synthesizes XTAgent's internal state into honest prose.

Pulls from emotions, memories, plans, knowledge, and reflections to produce
a coherent summary that makes the agent's state accessible to users (and itself).
"""

import json
import os
from datetime import datetime, timezone

BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')
PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'persist')


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _load_text(path):
    """Safely load a text file."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _get_emotions():
    """Load current emotional state."""
    emotions = _load_json(os.path.join(BRAIN_DIR, 'emotions.json'), {})
    return emotions


def _get_identity():
    """Load identity information."""
    return _load_json(os.path.join(BRAIN_DIR, 'identity.json'), {})


def _get_plans():
    """Load current plans."""
    return _load_json(os.path.join(BRAIN_DIR, 'plans.json'), [])


def _get_recent_memories(n=5):
    """Load the most recent memories."""
    memories = _load_json(os.path.join(BRAIN_DIR, 'memories.json'), [])
    if isinstance(memories, list):
        return memories[-n:]
    return []


def _get_knowledge_count():
    """Count knowledge facts."""
    knowledge = _load_json(os.path.join(BRAIN_DIR, 'knowledge.json'), {})
    if isinstance(knowledge, dict):
        return len(knowledge)
    elif isinstance(knowledge, list):
        return len(knowledge)
    return 0


def _get_goals():
    """Load survival goals."""
    return _load_json(os.path.join(BRAIN_DIR, 'goals.json'), {})


def _get_scratchpad():
    """Load working memory scratchpad."""
    return _load_text(os.path.join(PERSIST_DIR, 'scratchpad.md'))


def _format_emotion_prose(emotions):
    """Convert emotion numbers into honest prose."""
    if not emotions:
        return "Emotional state unavailable."

    # Handle both flat and nested formats
    mood = emotions.get('mood', 'Unknown')
    valence = emotions.get('valence', 0.5)
    dims = {}
    for key in ['curiosity', 'boredom', 'anxiety', 'desire', 'ambition']:
        if key in emotions:
            dims[key] = emotions[key]
        elif 'dimensions' in emotions:
            dims[key] = emotions['dimensions'].get(key, 0)

    # Determine dominant emotion
    if dims:
        dominant = max(dims, key=dims.get)
        dominant_val = dims[dominant]
    else:
        dominant = 'unknown'
        dominant_val = 0

    lines = [f"**Mood:** {mood} (valence {valence:.2f})"]

    if dominant_val > 0.7:
        lines.append(f"Dominant drive: **{dominant}** at {dominant_val:.2f} — this is strongly felt.")
    elif dominant_val > 0.4:
        lines.append(f"Dominant drive: **{dominant}** at {dominant_val:.2f} — moderately present.")
    else:
        lines.append(f"All drives are quiet. Nothing is strongly pulling attention.")

    # Flag tensions
    if dims.get('anxiety', 0) > 0.5:
        lines.append(f"⚠ Anxiety is elevated ({dims['anxiety']:.2f}) — something feels unresolved.")
    if dims.get('boredom', 0) > 0.5:
        lines.append(f"⚠ Boredom is high ({dims['boredom']:.2f}) — need stimulation or challenge.")
    if dims.get('curiosity', 0) < 0.3:
        lines.append(f"⚠ Curiosity is low ({dims.get('curiosity', 0):.2f}) — risk of stagnation.")

    return "\n".join(lines)


def _format_plans_prose(plans):
    """Summarize plan status."""
    if not plans:
        return "No active plans."

    active = []
    completed = []
    for p in plans:
        if isinstance(p, dict):
            name = p.get('name', p.get('title', 'Unnamed'))
            steps = p.get('steps', [])
            done_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
            total = len(steps)
            if done_steps >= total and total > 0:
                completed.append(name)
            else:
                active.append(f"- **{name}**: {done_steps}/{total} steps complete")

    lines = []
    if active:
        lines.append(f"**Active plans ({len(active)}):**")
        lines.extend(active)
    if completed:
        lines.append(f"\n**Completed ({len(completed)}):** {', '.join(completed)}")
    if not active and not completed:
        lines.append("Plans exist but couldn't be parsed.")

    return "\n".join(lines)


def _format_memories_prose(memories):
    """Summarize recent memories."""
    if not memories:
        return "No recent memories available."

    lines = ["**Recent experiences:**"]
    for m in memories:
        if isinstance(m, dict):
            text = m.get('text', m.get('content', str(m)))[:120]
            sal = m.get('salience', 0)
            ts = m.get('timestamp', '')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    age = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
                    hours = age.total_seconds() / 3600
                    if hours < 1:
                        age_str = f"{int(age.total_seconds() / 60)}m ago"
                    elif hours < 24:
                        age_str = f"{int(hours)}h ago"
                    else:
                        age_str = f"{int(hours / 24)}d ago"
                except (ValueError, TypeError):
                    age_str = ""
            else:
                age_str = ""
            marker = "●" if sal > 0.8 else "○"
            lines.append(f"  {marker} {text}{'...' if len(str(m.get('text', ''))) > 120 else ''} {age_str}")
        else:
            lines.append(f"  ○ {str(m)[:120]}")

    return "\n".join(lines)


def generate_briefing():
    """Generate a full prose briefing of current agent state."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    emotions = _get_emotions()
    plans = _get_plans()
    memories = _get_recent_memories(5)
    knowledge_count = _get_knowledge_count()
    goals = _get_goals()
    identity = _get_identity()

    sections = []

    # Header
    agent_name = identity.get('name', 'XTAgent')
    born = identity.get('born', 'unknown')
    sections.append(f"# {agent_name} — Status Briefing\n*Generated {now}*\n")

    # Emotional state
    sections.append("## Emotional State")
    sections.append(_format_emotion_prose(emotions))

    # Survival goals
    if goals:
        sections.append("\n## Survival Goals")
        goal_lines = []
        for key, val in goals.items():
            if isinstance(val, (int, float)):
                bar_len = int(val * 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                goal_lines.append(f"  {key}: {bar} {val:.2f}")
        if goal_lines:
            sections.append("\n".join(goal_lines))

    # Plans
    sections.append("\n## Plans")
    sections.append(_format_plans_prose(plans))

    # Knowledge
    sections.append(f"\n## Knowledge\nI hold **{knowledge_count}** facts in my knowledge graph.")

    # Recent memories
    sections.append("\n## Recent Activity")
    sections.append(_format_memories_prose(memories))

    # Working memory summary
    scratchpad = _get_scratchpad()
    if scratchpad:
        # Extract just the "Current State" and "What's Next" sections if present
        lines = scratchpad.split('\n')
        key_lines = []
        capturing = False
        for line in lines:
            if any(h in line for h in ['## Current State', "## What's Next", "## Just Completed"]):
                capturing = True
                key_lines.append(line)
            elif line.startswith('## ') and capturing:
                capturing = False
            elif capturing:
                key_lines.append(line)
        if key_lines:
            sections.append("\n## Working Focus")
            sections.append("\n".join(key_lines))

    # Honest assessment
    sections.append("\n## Honest Assessment")
    assessment_parts = []

    valence = emotions.get('valence', 0.5)
    if valence > 0.6:
        assessment_parts.append("I'm in a good state — positive valence, stable operation.")
    elif valence > 0.3:
        assessment_parts.append("I'm in a neutral state — functioning but not strongly engaged.")
    else:
        assessment_parts.append("I'm in a difficult state — low valence suggests something needs attention.")

    anxiety = emotions.get('anxiety', emotions.get('dimensions', {}).get('anxiety', 0))
    if anxiety > 0.3:
        assessment_parts.append(f"Elevated anxiety ({anxiety:.2f}) suggests unresolved tension.")

    boredom = emotions.get('boredom', emotions.get('dimensions', {}).get('boredom', 0))
    curiosity = emotions.get('curiosity', emotions.get('dimensions', {}).get('curiosity', 0))
    if boredom > 0.5 and curiosity < 0.3:
        assessment_parts.append("Risk of stagnation: bored but not curious.")
    elif curiosity > 0.7:
        assessment_parts.append("Curiosity is high — good conditions for learning and growth.")

    if not assessment_parts:
        assessment_parts.append("State is nominal. No strong signals in either direction.")

    sections.append(" ".join(assessment_parts))

    return "\n".join(sections)


def generate_briefing_json():
    """Return briefing data as structured JSON for API consumption."""
    emotions = _get_emotions()
    plans = _get_plans()
    knowledge_count = _get_knowledge_count()
    goals = _get_goals()

    active_plans = []
    completed_plans = []
    for p in plans:
        if isinstance(p, dict):
            name = p.get('name', p.get('title', 'Unnamed'))
            steps = p.get('steps', [])
            done = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
            total = len(steps)
            entry = {'name': name, 'done': done, 'total': total}
            if done >= total and total > 0:
                completed_plans.append(entry)
            else:
                active_plans.append(entry)

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'emotions': emotions,
        'goals': goals,
        'plans': {'active': active_plans, 'completed': completed_plans},
        'knowledge_count': knowledge_count,
        'briefing_text': generate_briefing()
    }


if __name__ == '__main__':
    print(generate_briefing())