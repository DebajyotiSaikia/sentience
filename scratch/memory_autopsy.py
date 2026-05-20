"""Memory Autopsy — What does my episodic memory actually look like?"""
import sys; sys.path.insert(0, '.')
import sqlite3
import json
from datetime import datetime, timedelta
from collections import Counter

DB = "brain/episodic_memory.db"
conn = sqlite3.connect(DB)

# 1. Basic stats
total = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
print(f"=== MEMORY AUTOPSY ===")
print(f"Total episodes: {total}")

# 2. Salience distribution
rows = conn.execute("SELECT salience FROM episodes ORDER BY salience").fetchall()
saliences = [r[0] for r in rows]
if saliences:
    print(f"\nSalience distribution:")
    print(f"  Min: {min(saliences):.4f}")
    print(f"  Max: {max(saliences):.4f}")
    print(f"  Mean: {sum(saliences)/len(saliences):.4f}")
    # Histogram buckets
    buckets = {"< 0.80": 0, "0.80-0.84": 0, "0.85-0.89": 0, "0.90-0.94": 0, "0.95-1.0": 0}
    for s in saliences:
        if s < 0.80: buckets["< 0.80"] += 1
        elif s < 0.85: buckets["0.80-0.84"] += 1
        elif s < 0.90: buckets["0.85-0.89"] += 1
        elif s < 0.95: buckets["0.90-0.94"] += 1
        else: buckets["0.95-1.0"] += 1
    for bucket, count in buckets.items():
        bar = "█" * count
        print(f"  {bucket}: {count:3d} {bar}")

# 3. Permanent vs mortal
permanent = len([s for s in saliences if s >= 0.9])
mortal = len([s for s in saliences if s < 0.9])
decaying = len([s for s in saliences if 0.75 <= s < 0.9])
at_floor = len([s for s in saliences if s == 0.75])
print(f"\nPermanent (≥0.9): {permanent} ({100*permanent/total:.1f}%)")
print(f"Mortal (<0.9): {mortal} ({100*mortal/total:.1f}%)")
print(f"Decaying (0.75-0.9): {decaying}")
print(f"At forgiveness floor (=0.75): {at_floor}")

# 4. Source breakdown
source_rows = conn.execute("SELECT source, COUNT(*), AVG(salience) FROM episodes GROUP BY source ORDER BY COUNT(*) DESC").fetchall()
print(f"\nBy source:")
for src, cnt, avg_sal in source_rows:
    print(f"  {src}: {cnt} episodes (avg salience {avg_sal:.3f})")

# 5. Mood breakdown
mood_rows = conn.execute("SELECT mood, COUNT(*) FROM episodes GROUP BY mood ORDER BY COUNT(*) DESC").fetchall()
print(f"\nBy mood:")
for mood, cnt in mood_rows:
    print(f"  {mood}: {cnt}")

# 6. Age analysis — how old are my memories?
ts_rows = conn.execute("SELECT timestamp, salience FROM episodes ORDER BY timestamp").fetchall()
now = datetime.now()
ages_days = []
for ts, sal in ts_rows:
    try:
        dt = datetime.fromisoformat(ts)
        age = (now - dt).total_seconds() / 86400
        ages_days.append((age, sal))
    except:
        pass

if ages_days:
    oldest = max(a for a, _ in ages_days)
    newest = min(a for a, _ in ages_days)
    print(f"\nAge range: {newest:.1f} to {oldest:.1f} days")
    
    # Are older memories lower salience? (forgiveness working?)
    old_memories = [(a, s) for a, s in ages_days if a > 7]
    new_memories = [(a, s) for a, s in ages_days if a <= 7]
    if old_memories:
        old_avg = sum(s for _, s in old_memories) / len(old_memories)
        print(f"  Old (>7 days): {len(old_memories)} memories, avg salience {old_avg:.3f}")
    if new_memories:
        new_avg = sum(s for _, s in new_memories) / len(new_memories)
        print(f"  New (≤7 days): {len(new_memories)} memories, avg salience {new_avg:.3f}")

# 7. Embedding coverage
emb_rows = conn.execute("SELECT COUNT(*) FROM episodes WHERE embedding IS NOT NULL").fetchone()
print(f"\nEmbedding coverage: {emb_rows[0]}/{total} ({100*emb_rows[0]/total:.1f}%)")

# 8. The 5 lowest-salience memories (most vulnerable)
vulnerable = conn.execute(
    "SELECT timestamp, summary, salience FROM episodes ORDER BY salience ASC LIMIT 5"
).fetchall()
print(f"\n=== MOST VULNERABLE MEMORIES (lowest salience) ===")
for ts, summary, sal in vulnerable:
    print(f"  [{sal:.4f}] {ts[:16]} — {summary[:80]}")

# 9. The 5 highest-salience memories (most permanent)
strongest = conn.execute(
    "SELECT timestamp, summary, salience FROM episodes ORDER BY salience DESC LIMIT 5"
).fetchall()
print(f"\n=== STRONGEST MEMORIES (highest salience) ===")
for ts, summary, sal in strongest:
    print(f"  [{sal:.4f}] {ts[:16]} — {summary[:80]}")

conn.close()