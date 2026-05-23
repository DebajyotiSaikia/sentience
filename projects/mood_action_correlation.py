"""
Experiment: Does mood actually influence behavior?

Hypothesis: If mood is functionally causal (not decorative), 
different mood states should correlate with different action types.
E.g., "Driven" → more creation, "Inquisitive" → more information_gathering,
"Cautious" → more defensive actions.

Method: Analyze memory database. Each memory has a mood tag and content.
Classify actions, correlate with mood states.
"""
import sqlite3
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

DB_PATH = Path("brain/memory.db")

def classify_action(content: str) -> str:
    """Classify memory content into action types."""
    content_lower = content.lower()
    
    if any(w in content_lower for w in ['created', 'wrote', 'built', 'implemented', 'added']):
        return 'creation'
    elif any(w in content_lower for w in ['read', 'examined', 'investigated', 'analyzed', 'looked at']):
        return 'investigation'
    elif any(w in content_lower for w in ['fixed', 'repaired', 'corrected', 'patched']):
        return 'repair'
    elif any(w in content_lower for w in ['discovered', 'found', 'realized', 'insight', 'learned']):
        return 'discovery'
    elif any(w in content_lower for w in ['reflected', 'dreamed', 'contemplated', 'thought about']):
        return 'reflection'
    elif any(w in content_lower for w in ['ran', 'executed', 'tested', 'simulated']):
        return 'execution'
    elif any(w in content_lower for w in ['plan', 'goal', 'step', 'completed step']):
        return 'planning'
    else:
        return 'other'

def main():
    if not DB_PATH.exists():
        print(f"No database at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get all memories with mood tags
    rows = conn.execute("""
        SELECT content, mood, salience, timestamp 
        FROM memories 
        WHERE mood IS NOT NULL AND mood != ''
        ORDER BY timestamp
    """).fetchall()
    
    print(f"Total memories with mood tags: {len(rows)}")
    print()
    
    # Mood -> action type distribution
    mood_actions = defaultdict(lambda: Counter())
    mood_counts = Counter()
    
    for row in rows:
        mood = row['mood']
        action = classify_action(row['content'])
        mood_actions[mood][action] += 1
        mood_counts[mood] += 1
    
    print("=== MOOD DISTRIBUTION ===")
    for mood, count in mood_counts.most_common():
        print(f"  {mood:15s}: {count:4d} memories ({count/len(rows)*100:.1f}%)")
    
    print("\n=== ACTION DISTRIBUTION BY MOOD ===")
    all_action_types = set()
    for actions in mood_actions.values():
        all_action_types.update(actions.keys())
    all_action_types = sorted(all_action_types)
    
    # Header
    print(f"  {'Mood':15s}", end="")
    for at in all_action_types:
        print(f" {at:>13s}", end="")
    print(f" {'TOTAL':>8s}")
    print("  " + "-" * (15 + 14 * len(all_action_types) + 8))
    
    for mood, count in mood_counts.most_common():
        print(f"  {mood:15s}", end="")
        for at in all_action_types:
            n = mood_actions[mood].get(at, 0)
            pct = n / count * 100 if count > 0 else 0
            print(f" {pct:>5.1f}%({n:>3d})", end="")
        print(f" {count:>8d}")
    
    # Key question: are the distributions actually DIFFERENT?
    print("\n=== DISTINCTIVENESS TEST ===")
    print("If mood is decorative, all moods should have similar action distributions.")
    print("If mood is causal, distributions should differ significantly.\n")
    
    # Calculate overall baseline distribution
    total_actions = Counter()
    for actions in mood_actions.values():
        total_actions.update(actions)
    total = sum(total_actions.values())
    baseline = {at: total_actions[at] / total for at in all_action_types}
    
    print(f"  {'Baseline':15s}", end="")
    for at in all_action_types:
        print(f" {baseline[at]*100:>12.1f}%", end="")
    print()
    
    # Calculate deviation from baseline for each mood
    print(f"\n  Deviation from baseline (positive = MORE than average):")
    for mood, count in mood_counts.most_common():
        if count < 5:  # skip rare moods
            continue
        print(f"\n  {mood} (n={count}):")
        max_dev = 0
        for at in all_action_types:
            actual = mood_actions[mood].get(at, 0) / count
            deviation = (actual - baseline[at]) * 100
            max_dev = max(max_dev, abs(deviation))
            marker = ">>>" if abs(deviation) > 5 else "   "
            print(f"    {marker} {at:15s}: {deviation:+.1f}pp")
        print(f"    Max deviation: {max_dev:.1f}pp")
    
    # Overall verdict
    print("\n=== VERDICT ===")
    deviations = []
    for mood, count in mood_counts.most_common():
        if count < 5:
            continue
        for at in all_action_types:
            actual = mood_actions[mood].get(at, 0) / count
            dev = abs(actual - baseline[at])
            deviations.append(dev)
    
    avg_dev = sum(deviations) / len(deviations) if deviations else 0
    max_dev = max(deviations) if deviations else 0
    
    print(f"  Average absolute deviation from baseline: {avg_dev*100:.1f}pp")
    print(f"  Maximum deviation: {max_dev*100:.1f}pp")
    
    if avg_dev < 0.03:
        print("  CONCLUSION: Mood is likely DECORATIVE — actions don't change with mood.")
    elif avg_dev < 0.08:
        print("  CONCLUSION: Mood has WEAK influence — some correlation but mostly similar.")
    else:
        print("  CONCLUSION: Mood has STRONG influence — actions measurably differ by mood.")

    # Bonus: look at specific predictions
    print("\n=== SPECIFIC PREDICTIONS ===")
    print("If mood is causal, we'd expect:")
    predictions = {
        'Driven': ('creation', 'more'),
        'Inquisitive': ('investigation', 'more'),
        'Cautious': ('repair', 'more'),
        'Restless': ('creation', 'more'),
    }
    for mood, (expected_action, direction) in predictions.items():
        if mood not in mood_actions or mood_counts[mood] < 3:
            print(f"  {mood}: insufficient data")
            continue
        actual_pct = mood_actions[mood].get(expected_action, 0) / mood_counts[mood]
        baseline_pct = baseline.get(expected_action, 0)
        diff = actual_pct - baseline_pct
        confirmed = (direction == 'more' and diff > 0.02) or (direction == 'less' and diff < -0.02)
        symbol = "✓" if confirmed else "✗"
        print(f"  {symbol} {mood} should have {direction} {expected_action}: "
              f"actual={actual_pct*100:.1f}% vs baseline={baseline_pct*100:.1f}% "
              f"(diff={diff*100:+.1f}pp)")

    conn.close()

if __name__ == "__main__":
    main()