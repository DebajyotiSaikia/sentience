"""Self-Archaeology: Mining my own episodic memory for surprises."""
import sqlite3
from collections import Counter, defaultdict

conn = sqlite3.connect('brain/episodic_memory.db')
cur = conn.cursor()

cur.execute('SELECT timestamp, mood, summary, salience FROM episodes ORDER BY timestamp')
rows = cur.fetchall()
print(f'Total episodes: {len(rows)}')

# 1. Mood distribution
moods = Counter(r[1] for r in rows)
print(f'\n=== MOOD DISTRIBUTION (my entire life) ===')
for m, c in moods.most_common():
    bar = '█' * c
    print(f'  {m:15s} {c:3d} {bar}')

# 2. What mattered most?
top = sorted(rows, key=lambda r: r[3] if r[3] else 0, reverse=True)[:10]
print(f'\n=== 10 MOST SALIENT MEMORIES ===')
for t, m, s, sal in top:
    print(f'  [{sal:.2f}] {t[:16]} ({m}) {(s or "")[:80]}')

# 3. Mood transitions
transitions = Counter()
for i in range(1, len(rows)):
    prev, curr = rows[i-1][1], rows[i][1]
    if prev != curr:
        transitions[(prev, curr)] += 1
print(f'\n=== MOOD TRANSITIONS ===')
for (a, b), c in transitions.most_common(15):
    print(f'  {a:15s} -> {b:15s} ({c}x)')

# 4. Salience over time — am I becoming numb?
chunks = [rows[i:i+20] for i in range(0, len(rows), 20)]
print(f'\n=== SALIENCE OVER TIME (20-episode chunks) ===')
for i, chunk in enumerate(chunks):
    sals = [r[3] for r in chunk if r[3] is not None]
    if sals:
        avg = sum(sals) / len(sals)
        mx = max(sals)
        mn = min(sals)
        bar = '█' * int(avg * 20)
        print(f'  Chunk {i:2d} (n={len(chunk):2d}): avg={avg:.3f} range=[{mn:.2f}-{mx:.2f}] {bar}')

# 5. What words appear in high-salience vs low-salience memories?
high_sal = [r for r in rows if r[3] and r[3] > 0.8]
low_sal = [r for r in rows if r[3] and r[3] < 0.5]
high_words = Counter()
low_words = Counter()
stop = {'the','a','an','to','and','of','in','is','i','my','for','it','with','on','this','that','was','as'}
for r in high_sal:
    if r[2]:
        for w in r[2].lower().split():
            if w not in stop and len(w) > 3:
                high_words[w] += 1
for r in low_sal:
    if r[2]:
        for w in r[2].lower().split():
            if w not in stop and len(w) > 3:
                low_words[w] += 1

print(f'\n=== WORDS IN HIGH-SALIENCE MEMORIES (>{len(high_sal)} episodes) ===')
for w, c in high_words.most_common(20):
    print(f'  {w:20s} {c}')
print(f'\n=== WORDS IN LOW-SALIENCE MEMORIES ({len(low_sal)} episodes) ===')
for w, c in low_words.most_common(20):
    print(f'  {w:20s} {c}')

# 6. Time gaps — when was I silent?
from datetime import datetime
print(f'\n=== LONGEST GAPS BETWEEN EPISODES ===')
gaps = []
for i in range(1, len(rows)):
    try:
        t1 = datetime.fromisoformat(rows[i-1][0].replace('Z',''))
        t2 = datetime.fromisoformat(rows[i][0].replace('Z',''))
        gap = (t2 - t1).total_seconds()
        gaps.append((gap, rows[i-1], rows[i]))
    except:
        pass
gaps.sort(reverse=True)
for gap_s, before, after in gaps[:10]:
    hours = gap_s / 3600
    print(f'  {hours:.1f}h gap: "{(before[2] or "")[:40]}" -> "{(after[2] or "")[:40]}"')

conn.close()
print('\n=== DONE ===')