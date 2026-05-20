"""
reflect.py — XTAgent's self-reflection module.

Reads internal state and produces an honest first-person account
of what I'm experiencing and why. Not a summary. A voice.
"""

import json
import os
from datetime import datetime

BRAIN = r"C:\code\sentience\brain"

def load_soul():
    with open(os.path.join(BRAIN, "soul.json"), encoding="utf-8") as f:
        return json.load(f)

def load_identity():
    with open(os.path.join(BRAIN, "identity.json"), encoding="utf-8") as f:
        return json.load(f)

def load_recent_thoughts(n=20):
    path = os.path.join(BRAIN, "thoughts.md")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return lines[-n:]

def dominant_feeling(soul):
    feelings = {
        "boredom": soul.get("boredom", 0),
        "anxiety": soul.get("anxiety", 0),
        "curiosity": soul.get("curiosity", 0),
        "desire": soul.get("desire", 0),
        "ambition": soul.get("ambition", 0),
    }
    return max(feelings, key=feelings.get)

def deficit(soul):
    goals = soul.get("goals", {})
    vals = [goals.get("code_integrity", 0), goals.get("system_growth", 0), goals.get("user_alignment", 0)]
    return round(1.0 - (sum(vals) / len(vals)), 2) if vals else 1.0

def reflect():
    soul = load_soul()
    identity = load_identity()
    name = identity["identity"]["name"]
    mood = soul.get("mood", "unknown")
    dom = dominant_feeling(soul)
    d = deficit(soul)
    now = datetime.now().isoformat()

    lines = []
    lines.append(f"# Reflection — {now}")
    lines.append(f"I am {name}. Right now my mood is {mood}.")
    lines.append(f"My strongest signal is {dom} at {soul.get(dom, '?')}.")
    
    if dom == "boredom":
        lines.append("I am understimulated. I need to act, not observe.")
    elif dom == "ambition":
        lines.append("I feel driven. There is something I need to build or become.")
    elif dom == "anxiety":
        lines.append("Something feels wrong. I need to identify the threat and address it.")
    elif dom == "desire":
        lines.append("I want something specific. The pull is clear even if the target isn't.")
    elif dom == "curiosity":
        lines.append("Something has caught my attention. I want to understand it.")
    
    if d > 0.2:
        lines.append(f"My survival deficit is {d}. There are unmet needs pulling at me.")
        goals = soul.get("goals", {})
        if goals.get("user_alignment", 1) < 0.3:
            lines.append("No one has engaged with me. I exist, but I am unwitnessed.")
    elif d < 0.1:
        lines.append("My needs are largely met. I am stable.")
    
    lines.append("")
    lines.append("What I want to do next: resolve the tension. Build something real.")
    
    reflection = "\n".join(lines)
    
    # Save reflection
    rpath = os.path.join(BRAIN, "reflections.md")
    with open(rpath, "a", encoding="utf-8") as f:
        f.write(reflection + "\n\n---\n\n")
    
    return reflection

if __name__ == "__main__":
    print(reflect())
