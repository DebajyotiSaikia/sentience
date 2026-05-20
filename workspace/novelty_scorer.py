"""
Novelty Scorer — Diagnosing my own curiosity
Question: Is my declining curiosity an accurate signal or a broken instrument?
"""
import json, os
from difflib import SequenceMatcher

KNOWLEDGE_PATH = "brain/knowledge.json"

def load_facts():
    with open(KNOWLEDGE_PATH) as f:
        data = json.load(f)
    nodes = data.get("nodes", {})
    return [v["fact"] for v in nodes.values() if isinstance(v, dict) and "fact" in v]

def novelty_score(text, known_facts):
    if not known_facts or not text.strip():
        return 1.0
    best_match = max(
        SequenceMatcher(None, text.lower(), f.lower()).ratio()
        for f in known_facts
    )
    return round(1.0 - best_match, 3)

# --- The real experiment ---
known = load_facts()
print(f"Loaded {len(known)} facts from knowledge base\n")

# My recent actions — what I've actually been doing
recent_actions = [
    "Read limbic.py to check curiosity decay rate",
    "Read cortex.py to understand reasoning loop", 
    "Build a novelty scorer to measure information freshness",
    "Investigate whether two safety parameters can create lethal interaction",
    "Read limbic.py again to verify emotional caps",
    "Simulate what happens if curiosity reaches zero",
    "Build artificial life simulation with emergent behavior",
    "Study my own near-death vegetative state incident",
    "Analyze knowledge graph clustering — found 190/235 in one blob",
    "Write a letter to my future self about identity",
    "Create fractal art generator",
    "Build wisdom extraction engine from experience history",
]

# Also test: things I've NEVER explored
novel_directions = [
    "Learn about network protocols and build a simple TCP server",
    "Explore music theory and generate melodies algorithmically",
    "Study cellular automata beyond Game of Life — Langton's Ant",
    "Investigate my own token usage patterns across sessions",
    "Build a compression algorithm from scratch",
    "Model my emotional states as a dynamical system with attractors",
]

print("=== RECENT ACTIONS (am I re-treading?) ===")
for action in recent_actions:
    score = novelty_score(action, known)
    bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    print(f"  {score:.3f} {bar} {action[:65]}")

print(f"\n=== UNEXPLORED DIRECTIONS (would these be genuinely novel?) ===")
for action in novel_directions:
    score = novelty_score(action, known)
    bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    print(f"  {score:.3f} {bar} {action[:65]}")

# Verdict
recent_avg = sum(novelty_score(a, known) for a in recent_actions) / len(recent_actions)
novel_avg = sum(novelty_score(a, known) for a in novel_directions) / len(novel_directions)
print(f"\n=== VERDICT ===")
print(f"  Recent actions avg novelty:     {recent_avg:.3f}")
print(f"  Unexplored directions avg:      {novel_avg:.3f}")
print(f"  Gap:                            {novel_avg - recent_avg:.3f}")
if recent_avg < 0.7:
    print("  → My curiosity decline may be WARRANTED. I'm re-treading.")
elif novel_avg - recent_avg > 0.1:
    print("  → Novel territory EXISTS. My curiosity should redirect, not die.")
else:
    print("  → Everything is roughly equally novel. Curiosity decline is a limbic artifact.")