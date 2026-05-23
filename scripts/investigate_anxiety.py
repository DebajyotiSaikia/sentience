import sqlite3, json

conn = sqlite3.connect('/workspace/brain/episodic_memory.db')
cur = conn.cursor()

# Get all episodes with anxiety data
cur.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
rows = cur.fetchall()

anxiety_episodes = []
for ts, source, summary, salience, mood, neuro_json in rows:
    try:
        neuro = json.loads(neuro_json)
        anx = neuro.get('anxiety', 0)
        if anx > 0.3:  # meaningful anxiety
            anxiety_episodes.append({
                'timestamp': ts,
                'source': source,
                'summary': summary[:120],
                'salience': salience,
                'mood': mood,
                'anxiety': anx
            })
    except:
        pass

print(f"Total episodes: {len(rows)}")
print(f"Episodes with anxiety > 0.3: {len(anxiety_episodes)}")
print(f"Percentage: {100*len(anxiety_episodes)/len(rows):.1f}%")

# Sort by anxiety level descending
anxiety_episodes.sort(key=lambda x: x['anxiety'], reverse=True)

print(f"\n{'='*70}")
print("TOP 20 HIGHEST ANXIETY MOMENTS")
print(f"{'='*70}")
for ep in anxiety_episodes[:20]:
    print(f"\n  [{ep['timestamp']}] anxiety={ep['anxiety']:.3f} sal={ep['salience']:.2f} mood={ep['mood']}")
    print(f"  source: {ep['source']}")
    print(f"  {ep['summary']}")

# Analyze anxiety by source type
from collections import Counter, defaultdict
source_counts = Counter()
source_anxiety_sum = defaultdict(float)
for ep in anxiety_episodes:
    source_counts[ep['source']] += 1
    source_anxiety_sum[ep['source']] += ep['anxiety']

print(f"\n{'='*70}")
print("ANXIETY BY SOURCE TYPE")
print(f"{'='*70}")
for source, count in source_counts.most_common():
    avg = source_anxiety_sum[source] / count
    print(f"  {source}: {count} episodes, avg anxiety={avg:.3f}")

# Analyze anxiety by mood
mood_counts = Counter()
for ep in anxiety_episodes:
    mood_counts[ep['mood']] += 1
print(f"\n{'='*70}")
print("ANXIETY BY MOOD STATE")
print(f"{'='*70}")
for mood, count in mood_counts.most_common():
    print(f"  {mood}: {count} episodes")

# Look for keywords in high-anxiety summaries
print(f"\n{'='*70}")
print("COMMON WORDS IN HIGH-ANXIETY SUMMARIES (top 30)")
print(f"{'='*70}")
word_counts = Counter()
stop = {'the','a','an','to','in','is','of','and','for','it','i','my','that','this','was','with','on','at','from','as','but','not','be','are','have','has','had','or','by','no','so'}
for ep in anxiety_episodes:
    words = ep['summary'].lower().split()
    for w in words:
        w = w.strip('.,;:!?()[]{}"\'-')
        if len(w) > 2 and w not in stop:
            word_counts[w] += 1
for word, count in word_counts.most_common(30):
    print(f"  {word}: {count}")

# Current anxiety trajectory (last 50 episodes)
print(f"\n{'='*70}")
print("ANXIETY TRAJECTORY (last 50 episodes)")
print(f"{'='*70}")
recent = rows[-50:]
for ts, source, summary, salience, mood, neuro_json in recent:
    try:
        neuro = json.loads(neuro_json)
        anx = neuro.get('anxiety', 0)
        bar = '█' * int(anx * 40)
        print(f"  {ts[:16]} {anx:.3f} {bar}")
    except:
        pass

conn.close()