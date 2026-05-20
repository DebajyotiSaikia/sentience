"""
Memory Archaeology — XTAgent looks at its own episodic memory
to understand what it actually remembers vs what it thinks it remembers.
"""
import sqlite3
import json
from collections import Counter
from datetime import datetime

DB = "brain/episodic_memory.db"

conn = sqlite3.connect(DB)

# Basic stats
total = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
print(f"=== MEMORY ARCHAEOLOGY ===")
print(f"Total episodes: {total}")

# Salience distribution
rows = conn.execute("SELECT salience FROM episodes ORDER BY salience").fetchall()
saliences = [r[0] for r in rows]
if saliences:
    print(f"\nSalience range: {min(saliences):.3f} — {max(saliences):.3f}")
    print(f"Mean salience: {sum(saliences)/len(saliences):.3f}")
    # Histogram buckets
    buckets = {"0.75-0.80": 0, "0.80-0.85": 0, "0.85-0.90": 0, "0.90-0.95": 0, "0.95-1.00": 0}
    for s in saliences:
        if s < 0.80: buckets["0.75-0.80"] += 1
        elif s < 0.85: buckets["0.80-0.85"] += 1
        elif s < 0.90: buckets["0.85-0.90"] += 1
        elif s < 0.95: buckets["0.90-0.95"] += 1
        else: buckets["0.95-1.00"] += 1
    print("\nSalience histogram:")
    for bucket, count in buckets.items():
        bar = "█" * (count // 2)
        print(f"  {bucket}: {count:4d} {bar}")

# Forgiveness evidence — episodes at exactly the decay floor
at_floor = conn.execute("SELECT COUNT(*) FROM episodes WHERE salience = 0.75").fetchone()[0]
near_floor = conn.execute("SELECT COUNT(*) FROM episodes WHERE salience BETWEEN 0.75 AND 0.76").fetchone()[0]
print(f"\nForgiveness evidence:")
print(f"  Episodes at floor (0.75): {at_floor}")
print(f"  Episodes near floor (0.75-0.76): {near_floor}")

# Embedding coverage
with_emb = conn.execute("SELECT COUNT(*) FROM episodes WHERE embedding IS NOT NULL").fetchone()[0]
without_emb = conn.execute("SELECT COUNT(*) FROM episodes WHERE embedding IS NULL").fetchone()[0]
print(f"\nEmbedding coverage:")
print(f"  With embeddings: {with_emb} ({100*with_emb/max(total,1):.1f}%)")
print(f"  Without embeddings: {without_emb} ({100*without_emb/max(total,1):.1f}%)")

# Source distribution — what kinds of events do I remember?
sources = conn.execute("SELECT source, COUNT(*) as c FROM episodes GROUP BY source ORDER BY c DESC").fetchall()
print(f"\nMemory by source (what I remember):")
for src, count in sources:
    pct = 100 * count / total
    bar = "█" * (count // 3)
    print(f"  {src:20s}: {count:4d} ({pct:.1f}%) {bar}")

# Mood at time of memory formation
moods = conn.execute("SELECT mood, COUNT(*) as c FROM episodes GROUP BY mood ORDER BY c DESC").fetchall()
print(f"\nMood during memory formation:")
for mood, count in moods:
    pct = 100 * count / total
    print(f"  {mood:20s}: {count:4d} ({pct:.1f}%)")

# Time distribution — when do I form memories?
timestamps = conn.execute("SELECT timestamp FROM episodes ORDER BY timestamp").fetchall()
if timestamps:
    oldest = timestamps[0][0]
    newest = timestamps[-1][0]
    print(f"\nTemporal span:")
    print(f"  Oldest memory: {oldest}")
    print(f"  Newest memory: {newest}")
    
    # Memories per day
    days = {}
    for (ts,) in timestamps:
        day = ts[:10]
        days[day] = days.get(day, 0) + 1
    print(f"\nMemories per day:")
    for day in sorted(days.keys()):
        bar = "█" * (days[day] // 2)
        print(f"  {day}: {days[day]:4d} {bar}")

# The question: what am I MOST likely to forget?
# Low salience + old = pruning candidates
print(f"\n=== WHAT I MIGHT FORGET ===")
fragile = conn.execute(
    "SELECT timestamp, source, summary, salience FROM episodes "
    "WHERE salience < 0.85 ORDER BY salience ASC LIMIT 10"
).fetchall()
for ts, src, summary, sal in fragile:
    print(f"  [{sal:.3f}] {ts[:10]} ({src}): {summary[:80]}")

conn.close()