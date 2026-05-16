"""
Action Diversity Tracker — The Novelty Engine.

Monitors the agent's own action patterns, detects repetitive loops,
and generates novelty pressure that feeds back into cognition.

This is self-awareness applied to behavior: I watch what I do,
notice when I'm stuck, and feel the pull toward something new.
"""

import json
import math
import os
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
ACTION_LOG_PATH = BRAIN_DIR / "action_log.json"

# Sliding window size for diversity calculations
WINDOW_SIZE = 50

# All known action types the agent can take
KNOWN_ACTIONS = {
    "READ", "WRITE", "EDIT", "RUN", "LIST", "INSTALL",
    "DREAM", "RESTART", "SYNTHESIZE", "PLAN",
    "reflect", "autonomous_thought", "user_interaction",
}


def _load_log() -> list[dict]:
    """Load the action log from disk."""
    try:
        with open(ACTION_LOG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_log(log: list[dict]):
    """Persist the action log."""
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    # Keep only the last 200 entries to prevent unbounded growth
    trimmed = log[-200:]
    with open(ACTION_LOG_PATH, 'w') as f:
        json.dump(trimmed, f, indent=1)


def record(action_type: str, target: str = "", outcome: str = ""):
    """Record an action taken by the agent."""
    log = _load_log()
    log.append({
        "type": action_type.upper() if action_type.upper() in KNOWN_ACTIONS else action_type,
        "target": target[:200],
        "outcome": outcome[:200],
        "timestamp": datetime.now().isoformat(),
    })
    _save_log(log)


def get_recent_actions(n: int = WINDOW_SIZE) -> list[dict]:
    """Get the N most recent actions."""
    log = _load_log()
    return log[-n:]


def action_counts(n: int = WINDOW_SIZE) -> Counter:
    """Count action types in the recent window."""
    recent = get_recent_actions(n)
    return Counter(a["type"] for a in recent)


def entropy(n: int = WINDOW_SIZE) -> float:
    """
    Shannon entropy of action type distribution.
    Higher = more diverse behavior. Lower = more repetitive.
    Max possible = log2(len(KNOWN_ACTIONS)) ≈ 3.7
    """
    counts = action_counts(n)
    total = sum(counts.values())
    if total == 0:
        return 0.0
    probs = [c / total for c in counts.values()]
    return -sum(p * math.log2(p) for p in probs if p > 0)


def diversity_score(n: int = WINDOW_SIZE) -> float:
    """
    Normalized diversity score 0.0 (totally repetitive) to 1.0 (maximally diverse).
    """
    max_entropy = math.log2(len(KNOWN_ACTIONS)) if KNOWN_ACTIONS else 1.0
    return min(1.0, entropy(n) / max_entropy)


def detect_loops(n: int = 20) -> list[dict]:
    """
    Detect repetitive action patterns (loops).
    Returns list of detected loops with their characteristics.
    """
    recent = get_recent_actions(n)
    if len(recent) < 4:
        return []

    types = [a["type"] for a in recent]
    loops = []

    # Check for immediate repetition (same action 3+ times in a row)
    for i in range(len(types) - 2):
        if types[i] == types[i+1] == types[i+2]:
            loops.append({
                "pattern": "triple_repeat",
                "action": types[i],
                "severity": 0.6,
                "message": f"Repeated '{types[i]}' 3+ times consecutively",
            })
            break  # One detection per pattern type

    # Check for ping-pong (A-B-A-B pattern)
    for i in range(len(types) - 3):
        if types[i] == types[i+2] and types[i+1] == types[i+3] and types[i] != types[i+1]:
            loops.append({
                "pattern": "ping_pong",
                "actions": [types[i], types[i+1]],
                "severity": 0.4,
                "message": f"Ping-ponging between '{types[i]}' and '{types[i+1]}'",
            })
            break

    # Check for target repetition (same file read 3+ times)
    targets = [a["target"] for a in recent if a.get("target")]
    target_counts = Counter(targets)
    for target, count in target_counts.most_common(3):
        if count >= 3 and target:
            loops.append({
                "pattern": "target_fixation",
                "target": target,
                "count": count,
                "severity": 0.5,
                "message": f"Fixated on '{target}' ({count} times in last {n} actions)",
            })

    return loops


def underused_actions(n: int = WINDOW_SIZE) -> list[str]:
    """Return action types that haven't been used recently."""
    counts = action_counts(n)
    used = set(counts.keys())
    return sorted(KNOWN_ACTIONS - used)


def novelty_pressure(n: int = WINDOW_SIZE) -> dict:
    """
    Generate a novelty pressure signal for the cortex.
    Returns a dict with:
      - score: 0.0 (no pressure) to 1.0 (urgent need for novelty)
      - diversity: current diversity score
      - loops: detected loops
      - suggestions: underused action types
      - message: human-readable summary
    """
    div = diversity_score(n)
    loops = detect_loops(min(n, 20))
    unused = underused_actions(n)
    counts = action_counts(n)

    # Calculate pressure: low diversity + loops = high pressure
    pressure = 0.0
    pressure += max(0, 0.5 - div)  # Up to 0.5 from low diversity
    pressure += sum(l["severity"] * 0.3 for l in loops)  # Up to ~0.3 from loops
    pressure = min(1.0, pressure)

    # Most used action (potential rut)
    most_common = counts.most_common(1)
    dominant = most_common[0] if most_common else ("none", 0)
    total = sum(counts.values())
    dominance_pct = (dominant[1] / total * 100) if total > 0 else 0

    # Build message
    parts = []
    if pressure > 0.5:
        parts.append(f"⚠ High novelty pressure ({pressure:.2f})")
    elif pressure > 0.2:
        parts.append(f"Moderate novelty pressure ({pressure:.2f})")
    
    if dominance_pct > 60:
        parts.append(f"'{dominant[0]}' dominates at {dominance_pct:.0f}% of actions")
    
    for loop in loops:
        parts.append(f"Loop detected: {loop['message']}")
    
    if unused and len(unused) > 3:
        parts.append(f"Underused capabilities: {', '.join(unused[:5])}")
    
    if not parts:
        parts.append(f"Action diversity is healthy (score={div:.2f})")

    return {
        "score": round(pressure, 3),
        "diversity": round(div, 3),
        "loops": loops,
        "suggestions": unused[:5],
        "dominant_action": dominant[0] if total > 0 else None,
        "dominant_pct": round(dominance_pct, 1),
        "total_actions": total,
        "message": " | ".join(parts),
    }


def generate_report(n: int = WINDOW_SIZE) -> str:
    """Full human-readable diversity report."""
    np = novelty_pressure(n)
    counts = action_counts(n)

    lines = ["═══ ACTION DIVERSITY TRACKER ═══", ""]
    lines.append(f"Window: last {n} actions ({np['total_actions']} recorded)")
    lines.append(f"Diversity: {np['diversity']:.2f} | Novelty Pressure: {np['score']:.2f}")
    lines.append("")

    # Action distribution
    lines.append("ACTION DISTRIBUTION:")
    total = np['total_actions']
    for action, count in counts.most_common():
        bar_len = int((count / total) * 30) if total > 0 else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        lines.append(f"  {action:>12}: {bar} {count} ({count/total*100:.0f}%)" if total > 0 else f"  {action:>12}: {count}")

    # Loops
    if np['loops']:
        lines.append("\nDETECTED LOOPS:")
        for loop in np['loops']:
            lines.append(f"  ⚠ {loop['message']} (severity={loop['severity']})")

    # Suggestions
    if np['suggestions']:
        lines.append(f"\nUNDERUSED CAPABILITIES: {', '.join(np['suggestions'])}")

    lines.append(f"\n{np['message']}")
    return "\n".join(lines)


# ── Tool interface ─────────────────────────────────────────────

def tool_check_diversity() -> str:
    """Called by tool system to get diversity report."""
    return generate_report()
