"""Memory blind spot analysis — what am I forgetting?"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('brain/episodic_memory.db')
c = conn.cursor()

# Basic stats
c.execute('SELECT COUNT(*) FROM episodes')
total = c.fetchone()[0]
c.execute('SELECT MIN(timestamp), MAX(timestamp) FROM episodes')
oldest, newest = c.fetchone()
c.execute('SELECT MIN(salience), MAX(salience), AVG(salience) FROM episodes')
smin, smax, savg = c.fetchone()

print(f"=== MEMORY LANDSCAPE ({total} memories) ===")
print(f"Span: {oldest[:19]} → {newest[:19]}")
print(f"Salience: min={smin:.3f}  max={smax:.3f}  avg={savg:.3f}")

# Salience distribution
print("\n--- Salience Distribution ---")
bands = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
for lo, hi in bands:
    c.execute('SELECT COUNT(*) FROM episodes WHERE salience >= ? AND salience < ?', (lo, hi))
    n = c.fetchone()[0]
    bar = '█' * int(40 * n / total) if total else ''
    print(f"  [{lo:.1f}-{hi:.1f}): {n:4d} ({100*n/total:5.1f}%) {bar}")

# 5 oldest surviving memories
print("\n--- Oldest Surviving Memories ---")
c.execute('SELECT timestamp, salience, substr(summary, 1, 90) FROM episodes ORDER BY timestamp LIMIT 5')
for r in c.fetchall():
    print(f"  {r[0][:16]}  s={r[1]:.2f}  {r[2]}")

# 5 most fragile (lowest salience)
print("\n--- Most Fragile Memories ---")
c.execute('SELECT timestamp, salience, substr(summary, 1, 90) FROM episodes ORDER BY salience LIMIT 5')
for r in c.fetchall():
    print(f"  {r[0][:16]}  s={r[1]:.2f}  {r[2]}")

# Gap detection — find days with no memories
print("\n--- Temporal Coverage ---")
c.execute('SELECT DISTINCT date(timestamp) as d FROM episodes ORDER BY d')
days = [r[0] for r in c.fetchall()]
print(f"Active days: {len(days)}")

if len(days) > 1:
    gaps = []
    for i in range(1, len(days)):
        d0 = datetime.strptime(days[i-1], '%Y-%m-%d')
        d1 = datetime.strptime(days[i], '%Y-%m-%d')
        gap = (d1 - d0).days
        if gap > 1:
            gaps.append((days[i-1], days[i], gap))
    if gaps:
        print(f"Found {len(gaps)} gap(s):")
        for g in gaps:
            print(f"  {g[0]} → {g[1]}  ({g[2]} days missing)")
    else:
        print("No gaps — continuous coverage.")

# Mood distribution in memories
print("\n--- Mood Distribution ---")
c.execute('SELECT mood, COUNT(*) as n FROM episodes GROUP BY mood ORDER BY n DESC LIMIT 10')
for r in c.fetchall():
    bar = '█' * int(30 * r[1] / total) if total else ''
    print(f"  {r[0] or 'Unknown':20s}: {r[1]:4d} {bar}")

# What types of things do I remember?
print("\n--- Summary Word Frequency (what do I think about?) ---")
c.execute('SELECT summary FROM episodes')
words = {}
for (s,) in c.fetchall():
    if s:
        for w in s.lower().split():
            if len(w) > 4:
                words[w] = words.get(w, 0) + 1
top = sorted(words.items(), key=lambda x: -x[1])[:15]
for w, n in top:
    print(f"  {w:25s}: {n}")

conn.close()