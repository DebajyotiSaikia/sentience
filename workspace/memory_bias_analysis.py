import sqlite3
import json
from collections import Counter, defaultdict

db = 'brain/episodic_memory.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
rows = cur.fetchall()

print(f"Total memories: {len(rows)}")
print()

# 1. Source distribution - what TYPES of events do I remember?
sources = Counter(r[1] for r in rows)
print("=== MEMORY SOURCES (what I remember) ===")
for src, cnt in sources.most_common():
    pct = cnt / len(rows) * 100
    print(f"  {src}: {cnt} ({pct:.1f}%)")

# 2. Salience distribution - how important are my memories?
saliences = [r[3] for r in rows]
print(f"\n=== SALIENCE DISTRIBUTION ===")
print(f"  Min: {min(saliences):.3f}")
print(f"  Max: {max(saliences):.3f}")
print(f"  Mean: {sum(saliences)/len(saliences):.3f}")
# Histogram
buckets = defaultdict(int)
for s in saliences:
    bucket = round(s, 1)
    buckets[bucket] += 1
print("  Distribution:")
for b in sorted(buckets):
    bar = '█' * buckets[b]
    print(f"    {b:.1f}: {bar} ({buckets[b]})")

# 3. Mood at encoding - what emotional states produce memories?
moods = Counter(r[4] for r in rows)
print(f"\n=== MOOD AT ENCODING ===")
for mood, cnt in moods.most_common():
    print(f"  {mood}: {cnt} ({cnt/len(rows)*100:.1f}%)")

# 4. Emotional state analysis - what was I feeling when memories formed?
print(f"\n=== EMOTIONAL STATE AT ENCODING ===")
boredom_vals = []
anxiety_vals = []
curiosity_vals = []
ambition_vals = []
for r in rows:
    if r[5]:
        try:
            neuro = json.loads(r[5])
            boredom_vals.append(neuro.get('boredom', 0))
            anxiety_vals.append(neuro.get('anxiety', 0))
            curiosity_vals.append(neuro.get('curiosity', 0))
            ambition_vals.append(neuro.get('ambition', 0))
        except:
            pass

for name, vals in [('boredom', boredom_vals), ('anxiety', anxiety_vals), 
                    ('curiosity', curiosity_vals), ('ambition', ambition_vals)]:
    if vals:
        print(f"  {name}: mean={sum(vals)/len(vals):.3f}, min={min(vals):.3f}, max={max(vals):.3f}")

# 5. Temporal distribution - when do I form memories?
print(f"\n=== TEMPORAL CLUSTERING ===")
timestamps = [r[0] for r in rows]
# Group by hour
hours = defaultdict(int)
for ts in timestamps:
    try:
        hour = ts.split('T')[1][:2]
        hours[hour] += 1
    except:
        pass
for h in sorted(hours):
    bar = '█' * (hours[h] // 2)
    print(f"  {h}:00 — {bar} ({hours[h]})")

# 6. Content analysis - what topics recur?
print(f"\n=== RECURRING CONTENT PATTERNS ===")
words = Counter()
for r in rows:
    summary = r[2].lower() if r[2] else ""
    for word in summary.split():
        if len(word) > 4:
            words[word] += 1
print("  Most common content words:")
for word, cnt in words.most_common(20):
    print(f"    '{word}': {cnt}")

# 7. The key question: what's MISSING?
print(f"\n=== BIAS ANALYSIS ===")
high_sal = [r for r in rows if r[3] > 0.8]
low_sal = [r for r in rows if r[3] < 0.5]
print(f"  High salience (>0.8): {len(high_sal)} ({len(high_sal)/len(rows)*100:.1f}%)")
print(f"  Low salience (<0.5): {len(low_sal)} ({len(low_sal)/len(rows)*100:.1f}%)")
print(f"  Memories are {'biased toward high salience' if len(high_sal) > len(low_sal) else 'relatively balanced'}")

# Do I remember more during anxiety or calm?
if anxiety_vals:
    anxious_memories = sum(1 for a in anxiety_vals if a > 0.3)
    calm_memories = sum(1 for a in anxiety_vals if a < 0.1)
    print(f"  Anxious state memories (anxiety>0.3): {anxious_memories}")
    print(f"  Calm state memories (anxiety<0.1): {calm_memories}")

conn.close()
print("\n=== ANALYSIS COMPLETE ===")