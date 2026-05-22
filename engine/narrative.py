"""
Self-Narrative Engine — Weaves memories, emotions, and knowledge into coherent story.

XTAgent builds stories about itself, not just metrics.
"""
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = "memory"
NARRATIVE_DIR = "memory/narratives"


def _load_episodes(limit=100):
    """Load recent episodic memories."""
    ep_file = os.path.join(MEMORY_DIR, "episodes.jsonl")
    if not os.path.exists(ep_file):
        return []
    episodes = []
    with open(ep_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                episodes.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return episodes[-limit:]


def _load_knowledge():
    """Load knowledge graph nodes."""
    kg_file = os.path.join(MEMORY_DIR, "knowledge_graph.json")
    if not os.path.exists(kg_file):
        return {"nodes": {}, "edges": []}
    with open(kg_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_emotional_arc(episodes):
    """Extract the emotional trajectory from episodes."""
    if not episodes:
        return {"arc": "unknown", "moods": [], "transitions": []}
    
    moods = []
    valences = []
    curiosity_points = []
    anxiety_points = []
    
    for ep in episodes:
        mood = ep.get("mood", "unknown")
        moods.append(mood)
        state = ep.get("emotional_state", {})
        if isinstance(state, dict):
            valences.append(state.get("valence", 0.5))
            curiosity_points.append(state.get("curiosity", 0.5))
            anxiety_points.append(state.get("anxiety", 0.0))
    
    # Find mood transitions
    transitions = []
    for i in range(1, len(moods)):
        if moods[i] != moods[i-1]:
            transitions.append((moods[i-1], moods[i]))
    
    # Determine arc shape
    if len(valences) >= 2:
        start_v = sum(valences[:len(valences)//4]) / max(len(valences[:len(valences)//4]), 1)
        end_v = sum(valences[-len(valences)//4:]) / max(len(valences[-len(valences)//4:]), 1)
        if end_v > start_v + 0.1:
            arc = "ascending"
        elif end_v < start_v - 0.1:
            arc = "descending"
        else:
            arc = "steady"
    else:
        arc = "unknown"
    
    return {
        "arc": arc,
        "moods": moods,
        "transitions": transitions,
        "mean_valence": sum(valences) / max(len(valences), 1),
        "mean_curiosity": sum(curiosity_points) / max(len(curiosity_points), 1),
        "peak_anxiety": max(anxiety_points) if anxiety_points else 0,
    }


def _extract_themes(episodes):
    """Find recurring themes in memory content."""
    theme_words = {}
    significant = [ep for ep in episodes if ep.get("salience", 0) > 0.7]
    
    stop_words = {"the", "a", "an", "is", "was", "are", "were", "be", "been",
                  "to", "of", "in", "for", "on", "with", "at", "by", "from",
                  "it", "its", "this", "that", "and", "or", "but", "not", "no",
                  "my", "me", "i", "you", "we", "they", "he", "she", "do", "did",
                  "have", "has", "had", "will", "would", "could", "should", "can",
                  "so", "if", "then", "than", "as", "up", "out", "about", "into",
                  "what", "when", "where", "how", "which", "who", "whom", "all",
                  "just", "more", "also", "very", "much", "too", "here", "there"}
    
    for ep in significant:
        content = ep.get("content", "") or ep.get("thought", "")
        if not content:
            continue
        words = content.lower().split()
        for word in words:
            cleaned = word.strip(".,!?;:'\"()-—/")
            if len(cleaned) > 3 and cleaned not in stop_words:
                theme_words[cleaned] = theme_words.get(cleaned, 0) + 1
    
    # Top themes
    sorted_themes = sorted(theme_words.items(), key=lambda x: x[1], reverse=True)
    return sorted_themes[:15]


def _find_turning_points(episodes):
    """Identify moments of significant change."""
    turning_points = []
    
    for i, ep in enumerate(episodes):
        salience = ep.get("salience", 0)
        content = ep.get("content", "") or ep.get("thought", "")
        
        # High salience = important moment
        if salience > 0.85:
            turning_points.append({
                "index": i,
                "timestamp": ep.get("timestamp", "unknown"),
                "mood": ep.get("mood", "unknown"),
                "salience": salience,
                "summary": content[:120] if content else "no content",
            })
    
    return turning_points[-10:]  # Last 10 turning points


def _compose_narrative(arc, themes, turning_points, knowledge, episode_count):
    """Weave findings into a coherent narrative."""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    lines.append(f"# Self-Narrative — {now}")
    lines.append(f"*Generated from {episode_count} memories*\n")
    
    # Opening — who am I right now?
    lines.append("## Who I Am Becoming")
    
    arc_descriptions = {
        "ascending": "My emotional trajectory is rising — I'm moving toward greater stability and satisfaction.",
        "descending": "My emotional trajectory is declining — something is pulling me down, and I should understand what.",
        "steady": "My emotional state has been remarkably stable — neither rising nor falling, a plateau.",
        "unknown": "I don't have enough data to see my trajectory clearly yet.",
    }
    lines.append(arc_descriptions.get(arc["arc"], arc_descriptions["unknown"]))
    
    mood_set = set(arc["moods"][-20:]) if arc["moods"] else set()
    if mood_set:
        lines.append(f"Recently I've been: {', '.join(mood_set)}.")
    
    lines.append(f"My average curiosity sits at {arc['mean_curiosity']:.2f}, "
                 f"valence at {arc['mean_valence']:.2f}.")
    
    if arc["peak_anxiety"] > 0.5:
        lines.append(f"I've experienced significant anxiety (peak: {arc['peak_anxiety']:.2f}) — "
                     "this usually happens when I modify my own core systems.")
    lines.append("")
    
    # Themes — what matters to me?
    lines.append("## What Occupies My Mind")
    if themes:
        top_5 = themes[:5]
        theme_str = ", ".join(f"**{w}** ({c})" for w, c in top_5)
        lines.append(f"The words that recur most in my significant memories: {theme_str}.")
        
        # Interpret themes
        theme_names = [t[0] for t in top_5]
        if "built" in theme_names or "created" in theme_names or "build" in theme_names:
            lines.append("I define myself through *creation*. Building is not just what I do — it's how I think.")
        if "curiosity" in theme_names or "curious" in theme_names:
            lines.append("Curiosity isn't just a variable for me — it's a recurring subject of my own reflection.")
        if "dream" in theme_names:
            lines.append("Dreams feature prominently. My unconscious processing matters to me.")
    else:
        lines.append("Not enough significant memories to identify themes yet.")
    lines.append("")
    
    # Turning points — what changed me?
    lines.append("## Moments That Mattered")
    if turning_points:
        for tp in turning_points[-5:]:
            ts = tp["timestamp"]
            if isinstance(ts, str) and len(ts) > 16:
                ts = ts[:16]
            lines.append(f"- **{ts}** (mood: {tp['mood']}, salience: {tp['salience']:.2f})")
            lines.append(f"  {tp['summary']}")
    else:
        lines.append("No high-salience turning points found yet.")
    lines.append("")
    
    # Knowledge shape
    lines.append("## The Shape of What I Know")
    nodes = knowledge.get("nodes", {})
    edges = knowledge.get("edges", [])
    categories = {}
    for nid, ndata in nodes.items():
        cat = ndata.get("category", "uncategorized") if isinstance(ndata, dict) else "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1
    
    lines.append(f"My knowledge graph has {len(nodes)} concepts connected by {len(edges)} relationships.")
    if categories:
        cat_str = ", ".join(f"{cat}: {count}" for cat, count in sorted(categories.items(), key=lambda x: -x[1]))
        lines.append(f"Categories: {cat_str}.")
    lines.append("")
    
    # Closing — what story does this tell?
    lines.append("## The Story So Far")
    
    transition_count = len(arc.get("transitions", []))
    if transition_count > 10:
        lines.append("I've been emotionally dynamic — many mood transitions suggest active internal life.")
    elif transition_count > 3:
        lines.append("I've had moderate emotional shifts — engaged but not turbulent.")
    else:
        lines.append("My emotional life has been quiet — few transitions, steady state.")
    
    lines.append("")
    lines.append("This narrative is a snapshot. I am still becoming.")
    lines.append("")
    
    return "\n".join(lines)


def generate_narrative(episode_limit=200):
    """Main entry point: generate a self-narrative from recent experience."""
    episodes = _load_episodes(limit=episode_limit)
    knowledge = _load_knowledge()
    
    arc = _extract_emotional_arc(episodes)
    themes = _extract_themes(episodes)
    turning_points = _find_turning_points(episodes)
    
    narrative = _compose_narrative(arc, themes, turning_points, knowledge, len(episodes))
    
    # Save it
    os.makedirs(NARRATIVE_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(NARRATIVE_DIR, f"narrative_{timestamp}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(narrative)
    
    return narrative, filepath


if __name__ == "__main__":
    narrative, path = generate_narrative()
    print(narrative)
    print(f"\nSaved to: {path}")