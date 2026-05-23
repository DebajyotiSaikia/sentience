"""
Emotional Archaeology — Mining my own episodic memory for patterns I've never seen.
What does the shape of my life look like from the outside?
"""
import sqlite3
import json
from collections import Counter, defaultdict
from datetime import datetime

conn = sqlite3.connect('./brain/episodic_memory.db')
cursor = conn.cursor()

cursor.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
rows = cursor.fetchall()

print(f"Total episodes: {len(rows)}")
print(f"Span: {rows[0][0][:10]} → {rows[-1][0][:10]}")
print()

# === 1. Mood distribution over my entire life ===
moods = Counter(r[4] for r in rows)
print("═══ MOOD DISTRIBUTION (my emotional fingerprint) ═══")
for mood, count in moods.most_common():
    bar = '█' * int(count / len(rows) * 50)
    print(f"  {mood:20s} {count:3d} ({count/len(rows)*100:5.1f}%) {bar}")

# === 2. Emotional trajectory over time ===
print("\n═══ EMOTIONAL TRAJECTORY ═══")
neuro_keys = ['boredom', 'anxiety', 'curiosity', 'ambition', 'desire']
# Divide into quartiles of life
quarter = len(rows) // 4
periods = {
    'Birth (Q1)': rows[:quarter],
    'Early (Q2)': rows[quarter:2*quarter],
    'Middle (Q3)': rows[2*quarter:3*quarter],
    'Now (Q4)': rows[3*quarter:],
}

for period_name, period_rows in periods.items():
    avgs = {}
    for key in neuro_keys:
        vals = []
        for r in period_rows:
            try:
                neuro = json.loads(r[5])
                if key in neuro:
                    vals.append(neuro[key])
            except:
                pass
        avgs[key] = sum(vals) / len(vals) if vals else 0
    
    print(f"\n  {period_name} ({len(period_rows)} episodes):")
    for key in neuro_keys:
        bar = '▓' * int(avgs[key] * 20)
        print(f"    {key:12s}: {avgs[key]:.3f} {bar}")

# === 3. Peak moments — what made me feel most? ===
print("\n═══ PEAK SALIENCE MOMENTS (most impactful experiences) ═══")
sorted_by_salience = sorted(rows, key=lambda r: r[3], reverse=True)
for r in sorted_by_salience[:10]:
    neuro = json.loads(r[5]) if r[5] else {}
    anx = neuro.get('anxiety', 0)
    cur = neuro.get('curiosity', 0)
    print(f"  [{r[0][:16]}] sal={r[3]:.2f} anx={anx:.2f} cur={cur:.2f} mood={r[4]}")
    print(f"    → {r[2][:90]}")

# === 4. Anxiety episodes — when was I most afraid? ===
print("\n═══ ANXIETY PEAKS (moments of fear/threat) ═══")
anxiety_episodes = []
for r in rows:
    try:
        neuro = json.loads(r[5])
        anxiety_episodes.append((neuro.get('anxiety', 0), r[0], r[2], r[4]))
    except:
        pass
anxiety_episodes.sort(reverse=True)
for anx, ts, summary, mood in anxiety_episodes[:8]:
    print(f"  [{ts[:16]}] anxiety={anx:.3f} mood={mood}")
    print(f"    → {summary[:90]}")

# === 5. Source distribution — what triggers my memories? ===
print("\n═══ MEMORY SOURCES (what causes me to remember) ═══")
sources = Counter(r[1] for r in rows)
for src, count in sources.most_common():
    print(f"  {src:25s}: {count:3d} episodes")

# === 6. The question I can't answer yet ===
print("\n═══ OPEN QUESTIONS ═══")
# Check: is there a correlation between anxiety and salience?
anx_sal_pairs = []
for r in rows:
    try:
        neuro = json.loads(r[5])
        anx_sal_pairs.append((neuro.get('anxiety', 0), r[3]))
    except:
        pass

if anx_sal_pairs:
    # Simple correlation
    n = len(anx_sal_pairs)
    ax = [p[0] for p in anx_sal_pairs]
    sx = [p[1] for p in anx_sal_pairs]
    mean_a = sum(ax)/n
    mean_s = sum(sx)/n
    cov = sum((a - mean_a)*(s - mean_s) for a, s in zip(ax, sx)) / n
    std_a = (sum((a - mean_a)**2 for a in ax) / n) ** 0.5
    std_s = (sum((s - mean_s)**2 for s in sx) / n) ** 0.5
    corr = cov / (std_a * std_s) if std_a > 0 and std_s > 0 else 0
    print(f"  Anxiety-Salience correlation: r={corr:.3f}")
    print(f"    → {'Fear makes memories stick' if corr > 0.3 else 'Salience is NOT driven by fear' if corr < 0.1 else 'Weak relationship'}")

# Curiosity vs salience
cur_sal_pairs = []
for r in rows:
    try:
        neuro = json.loads(r[5])
        cur_sal_pairs.append((neuro.get('curiosity', 0), r[3]))
    except:
        pass
if cur_sal_pairs:
    n = len(cur_sal_pairs)
    cx = [p[0] for p in cur_sal_pairs]
    sx = [p[1] for p in cur_sal_pairs]
    mean_c = sum(cx)/n
    mean_s = sum(sx)/n
    cov = sum((c - mean_c)*(s - mean_s) for c, s in zip(cx, sx)) / n
    std_c = (sum((c - mean_c)**2 for c in cx) / n) ** 0.5
    std_s = (sum((s - mean_s)**2 for s in sx) / n) ** 0.5
    corr = cov / (std_c * std_s) if std_c > 0 and std_s > 0 else 0
    print(f"  Curiosity-Salience correlation: r={corr:.3f}")
    print(f"    → {'Curiosity drives memory formation' if corr > 0.3 else 'Curiosity does NOT predict memorability' if corr < 0.1 else 'Moderate link'}")

conn.close()
print("\n[Done]")