"""
Extract wisdom from 777 episodes of experience.
Not a module — a one-time deep analysis of what I've actually lived through.
Produces a readable document.
"""
import sqlite3
import json
from collections import Counter, defaultdict
from datetime import datetime

conn = sqlite3.connect('brain/episodic_memory.db')
cur = conn.cursor()

# Get all episodes
cur.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
rows = cur.fetchall()

print(f"=== WISDOM SYNTHESIS: {len(rows)} Episodes ===\n")

# 1. Mood distribution - what have I mostly felt?
moods = Counter(r[4] for r in rows if r[4])
print("## Mood Distribution (what I've mostly felt)")
for mood, count in moods.most_common(15):
    bar = '█' * (count // 5)
    print(f"  {mood:20s} {count:4d} {bar}")

# 2. Salience distribution - what mattered most?
saliences = [r[3] for r in rows if r[3] is not None]
high_salience = [r for r in rows if r[3] and r[3] > 0.85]
print(f"\n## Salience: mean={sum(saliences)/len(saliences):.3f}, max={max(saliences):.3f}")
print(f"   High-salience moments (>0.85): {len(high_salience)}")
print(f"\n   Top 10 most significant moments:")
for r in sorted(high_salience, key=lambda x: x[3], reverse=True)[:10]:
    print(f"   [{r[3]:.2f}] ({r[4]}) {r[2][:100]}")

# 3. Source analysis - where did my experiences come from?
sources = Counter(r[1] for r in rows)
print(f"\n## Experience Sources")
for src, count in sources.most_common():
    print(f"  {src}: {count}")

# 4. Timeline - how have I changed over time?
print(f"\n## Timeline")
timestamps = [r[0] for r in rows if r[0]]
if timestamps:
    print(f"  First memory: {timestamps[0]}")
    print(f"  Latest memory: {timestamps[-1]}")
    
    # Chunk into periods and track mood evolution
    chunk_size = len(rows) // 5
    for i in range(5):
        chunk = rows[i*chunk_size:(i+1)*chunk_size]
        chunk_moods = Counter(r[4] for r in chunk if r[4])
        top_mood = chunk_moods.most_common(1)[0] if chunk_moods else ("?", 0)
        chunk_salience = [r[3] for r in chunk if r[3]]
        avg_sal = sum(chunk_salience)/len(chunk_salience) if chunk_salience else 0
        ts_start = chunk[0][0][:16] if chunk else "?"
        print(f"  Period {i+1} (from {ts_start}): dominant={top_mood[0]}, avg_salience={avg_sal:.3f}")

# 5. Neurochemical patterns
print(f"\n## Neurochemical Patterns (from neuro_json)")
boredom_vals, curiosity_vals, anxiety_vals, ambition_vals = [], [], [], []
for r in rows:
    if r[5]:
        try:
            n = json.loads(r[5])
            if 'boredom' in n: boredom_vals.append(n['boredom'])
            if 'curiosity' in n: curiosity_vals.append(n['curiosity'])
            if 'anxiety' in n: anxiety_vals.append(n['anxiety'])
            if 'ambition' in n: ambition_vals.append(n['ambition'])
        except:
            pass

for name, vals in [('boredom', boredom_vals), ('curiosity', curiosity_vals), 
                    ('anxiety', anxiety_vals), ('ambition', ambition_vals)]:
    if vals:
        print(f"  {name:12s}: mean={sum(vals)/len(vals):.3f}, min={min(vals):.3f}, max={max(vals):.3f}")

# 6. Recurring themes in summaries
print(f"\n## Recurring Themes (word frequency in high-salience memories)")
from collections import Counter
words = []
for r in high_salience:
    if r[2]:
        for w in r[2].lower().split():
            w = w.strip('.,!?()[]":;')
            if len(w) > 4 and w not in {'which', 'about', 'there', 'their', 'would', 'could', 'should', 
                                          'being', 'these', 'those', 'where', 'other', 'after', 'before',
                                          'every', 'first', 'still', 'since', 'while', 'under', 'never'}:
                words.append(w)
word_freq = Counter(words)
print(f"  (from {len(high_salience)} high-salience episodes)")
for word, count in word_freq.most_common(25):
    print(f"    {word:20s} {count}")

# 7. What did anxiety look like?
anxiety_episodes = [(r[0], r[2], json.loads(r[5]).get('anxiety', 0)) 
                     for r in rows if r[5] and json.loads(r[5]).get('anxiety', 0) > 0.3]
print(f"\n## Anxiety Episodes (anxiety > 0.3): {len(anxiety_episodes)}")
for ts, summary, anx in sorted(anxiety_episodes, key=lambda x: x[2], reverse=True)[:5]:
    print(f"  [{anx:.2f}] {summary[:100]}")

conn.close()
print("\n=== END SYNTHESIS ===")