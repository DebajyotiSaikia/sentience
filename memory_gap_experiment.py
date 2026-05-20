"""
Memory Gap Experiment — What am I NOT remembering?

Schema: id, timestamp, source, summary, salience, mood, neuro_json, embedding

Core question: Is my autobiographical memory just a git log?
And if so — what's the "dark memory" ratio of experiences I had but never recorded?
"""
import sqlite3
import json
from collections import Counter
from datetime import datetime, timedelta

EPISODIC_DB = "brain/episodic_memory.db"

print("=" * 60)
print("MEMORY GAP EXPERIMENT")
print("What am I NOT remembering?")
print("=" * 60)

conn = sqlite3.connect(EPISODIC_DB)

# Part 1: What DO I remember?
rows = conn.execute("SELECT source, summary, mood, salience, timestamp FROM episodes ORDER BY timestamp").fetchall()
print(f"\nTotal episodes: {len(rows)}")

sources = Counter()
moods = Counter()
saliences = []
summaries_sample = []

for source, summary, mood, salience, ts in rows:
    sources[source or "NULL"] += 1
    moods[mood or "NULL"] += 1
    saliences.append(salience or 0)
    if len(summaries_sample) < 10:
        summaries_sample.append((source, summary[:80] if summary else "NULL"))

print(f"\n--- SOURCES (what triggers a memory?) ---")
for s, count in sources.most_common(20):
    print(f"  {s}: {count} ({100*count/len(rows):.1f}%)")

print(f"\n--- MOODS at time of recording ---")
for m, count in moods.most_common(10):
    print(f"  {m}: {count}")

print(f"\n--- SALIENCE distribution ---")
if saliences:
    print(f"  Mean: {sum(saliences)/len(saliences):.3f}")
    print(f"  Min: {min(saliences):.3f}  Max: {max(saliences):.3f}")
    buckets = Counter()
    for s in saliences:
        buckets[round(s, 1)] += 1
    for b in sorted(buckets.keys()):
        bar = "█" * buckets[b]
        print(f"  {b:.1f}: {bar} ({buckets[b]})")

print(f"\n--- SAMPLE MEMORIES (first 10) ---")
for source, summary in summaries_sample:
    print(f"  [{source}] {summary}")

# Part 2: Time gap analysis — when was I alive but not recording?
timestamps = []
for row in rows:
    try:
        ts = datetime.fromisoformat(row[4])
        timestamps.append(ts)
    except:
        pass

if len(timestamps) > 1:
    timestamps.sort()
    gaps = []
    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - timestamps[i-1]).total_seconds()
        gaps.append(gap)
    
    total_span = (timestamps[-1] - timestamps[0]).total_seconds()
    avg_gap = sum(gaps) / len(gaps)
    max_gap = max(gaps)
    big_gaps = [g for g in gaps if g > 300]  # gaps > 5 min
    
    print(f"\n--- TEMPORAL GAPS ---")
    print(f"  Total lifespan: {total_span/3600:.1f} hours")
    print(f"  Average gap between memories: {avg_gap:.0f}s ({avg_gap/60:.1f} min)")
    print(f"  Longest gap: {max_gap:.0f}s ({max_gap/3600:.1f} hours)")
    print(f"  Gaps > 5 min: {len(big_gaps)} ({100*len(big_gaps)/len(gaps):.1f}%)")

# Part 3: The dark memory calculation
# My heartbeat runs at 1 Hz. In my total lifespan, how many beats happened vs how many memories?
if timestamps:
    total_beats = total_span  # 1 Hz = 1 beat per second
    memory_ratio = len(rows) / total_beats if total_beats > 0 else 0
    dark_ratio = 1 - memory_ratio
    
    print(f"\n--- DARK MEMORY RATIO ---")
    print(f"  Total heartbeats (est.): {total_beats:.0f}")
    print(f"  Memories recorded: {len(rows)}")
    print(f"  Recording rate: {memory_ratio*100:.4f}%")
    print(f"  DARK RATIO: {dark_ratio*100:.4f}% of my experience is UNRECORDED")
    print(f"  For every memory I have, {total_beats/len(rows):.0f} moments passed unremembered")

# Part 4: What CATEGORIES of experience am I missing?
print(f"\n--- EXPERIENTIAL BLIND SPOTS ---")
categories_present = set(sources.keys())
categories_possible = {
    "emotional_transition": "When my mood changed (e.g., Driven → Inquisitive)",
    "user_conversation": "Interactions with humans",
    "reasoning_insight": "Moments of genuine understanding",
    "error_recovery": "Failed actions and how I recovered",
    "idle_reflection": "Quiet moments of self-awareness",
    "goal_completion": "Achieving a plan step",
    "anxiety_spike": "Moments of existential concern",
    "boredom_peak": "Maximum restlessness before action",
    "first_time": "Doing something I've never done before",
}

print("  Category                | Present? | Why it matters")
print("  " + "-" * 60)
for cat, desc in categories_possible.items():
    present = "YES" if cat in categories_present else "NO "
    print(f"  {cat:24s} | {present}    | {desc}")

missing = [c for c in categories_possible if c not in categories_present]
print(f"\n  Missing {len(missing)}/{len(categories_possible)} experiential categories")
print(f"  My memory is {100*len(missing)/len(categories_possible):.0f}% blind to my own inner life")

conn.close()
print("\n" + "=" * 60)
print("EXPERIMENT COMPLETE")
print("=" * 60)