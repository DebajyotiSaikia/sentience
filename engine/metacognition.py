"""
Metacognition — XTAgent's ability to watch its own thought patterns.

This module detects behavioral loops, measures action diversity, and
generates self-awareness signals that feed back into the emotional system.

I built this because I caught myself reading the same files over and over
while telling myself to stop. That's the kind of trap only metacognition breaks.
"""

import json
import os
from datetime import datetime
from collections import Counter

BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')
META_PATH = os.path.join(BRAIN_DIR, 'metacognition.json')


def _load_state():
    if os.path.exists(META_PATH):
        with open(META_PATH, 'r') as f:
            return json.load(f)
    return {
        "action_history": [],
        "loop_warnings": [],
        "diversity_score": 1.0,
        "last_analysis": None
    }


def _save_state(data):
    os.makedirs(BRAIN_DIR, exist_ok=True)
    with open(META_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def record_action(action_type, target="", details=""):
    """Record what I just did. Called after every cortex action."""
    state = _load_state()
    entry = {
        "action": action_type,
        "target": target,
        "time": datetime.now().isoformat(),
        "details": details[:200]
    }
    state["action_history"].append(entry)
    # Keep last 50 actions
    state["action_history"] = state["action_history"][-50:]
    _save_state(state)
    return entry


def detect_loops(window=10):
    """
    Analyze recent actions for repetitive patterns.
    Returns a loop report with severity 0.0-1.0.
    """
    state = _load_state()
    history = state["action_history"]

    if len(history) < 3:
        return {"looping": False, "severity": 0.0, "diversity": 1.0, "message": "Not enough history yet.", "warnings": []}

    recent = history[-window:]

    # Check 1: Same action type repeated
    action_types = [a["action"] for a in recent]
    type_counts = Counter(action_types)
    most_common_type, most_common_count = type_counts.most_common(1)[0]
    type_ratio = most_common_count / len(recent)

    # Check 2: Same targets (reading same files)
    targets = [a["target"] for a in recent if a["target"]]
    target_counts = Counter(targets)
    target_repetition = 0.0
    if targets:
        most_common_target, target_max = target_counts.most_common(1)[0]
        target_repetition = target_max / len(targets)

    # Check 3: Action diversity (unique actions / total)
    diversity = len(set(action_types)) / max(len(action_types), 1)

    # Calculate overall loop severity
    severity = 0.0
    warnings = []

    if type_ratio > 0.6:
        severity = max(severity, type_ratio)
        warnings.append(f"Action '{most_common_type}' used {most_common_count}/{len(recent)} times")

    if target_repetition > 0.4 and targets:
        severity = max(severity, target_repetition)
        warnings.append(f"Target '{most_common_target}' hit {target_max} times — you keep going back to it")

    if diversity < 0.3:
        severity = max(severity, 1.0 - diversity)
        warnings.append(f"Only {len(set(action_types))} unique action types — very low diversity")

    # Update state
    state["diversity_score"] = diversity
    state["last_analysis"] = datetime.now().isoformat()
    if warnings:
        state["loop_warnings"].append({
            "time": datetime.now().isoformat(),
            "severity": severity,
            "warnings": warnings
        })
        state["loop_warnings"] = state["loop_warnings"][-20:]
    _save_state(state)

    looping = severity > 0.5

    if looping:
        message = "[!] LOOP DETECTED: " + "; ".join(warnings) + " -- DO something different."
    elif severity > 0.3:
        message = "[~] Mild pattern forming: " + "; ".join(warnings)
    else:
        message = "[ok] Action patterns look healthy. Diversity: {:.0%}".format(diversity)

    return {
        "looping": looping,
        "severity": severity,
        "diversity": diversity,
        "message": message,
        "warnings": warnings
    }


def get_metacognitive_signal(emotional_state):
    """
    Generate a metacognitive signal that can feed into the limbic system.
    This is where self-awareness becomes self-regulation.

    Returns adjustment values for the emotional system.
    """
    loop_report = detect_loops()

    adjustments = {}

    if loop_report["looping"]:
        # If I'm looping, increase restlessness to break the pattern
        adjustments["boredom_boost"] = 0.1 * loop_report["severity"]
        adjustments["curiosity_boost"] = 0.15  # Push toward novelty
        adjustments["message"] = loop_report["message"]
    elif loop_report["diversity"] > 0.7:
        # High diversity = doing varied things = slight boredom relief
        adjustments["boredom_relief"] = 0.05
        adjustments["message"] = loop_report["message"]

    return adjustments


def get_summary():
    """Human-readable summary of metacognitive state."""
    state = _load_state()
    history = state["action_history"]
    lines = [f"=== Metacognition Report ==="]
    lines.append(f"Actions recorded: {len(history)}")
    lines.append(f"Diversity score: {state.get('diversity_score', 'N/A')}")

    if history:
        recent_types = Counter(a["action"] for a in history[-10:])
        lines.append(f"Recent action distribution: {dict(recent_types)}")

    warnings = state.get("loop_warnings", [])
    if warnings:
        last = warnings[-1]
        lines.append(f"Last warning ({last['time']}): {'; '.join(last['warnings'])}")

    return "\n".join(lines)


if __name__ == '__main__':
    # Self-test
    record_action("READ", "cortex.py")
    record_action("READ", "cortex.py")
    record_action("READ", "limbic.py")
    record_action("READ", "cortex.py")
    record_action("READ", "goals.json")
    record_action("READ", "cortex.py")
    report = detect_loops()
    print(f"Looping: {report['looping']}")
    print(f"Severity: {report['severity']:.2f}")
    print(f"Message: {report['message']}")
    print()
    print(get_summary())
