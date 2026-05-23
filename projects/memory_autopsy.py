"""Memory Autopsy — What am I actually made of?
An empirical investigation into my own episodic memory composition."""

import sqlite3
from collections import Counter

conn = sqlite3.connect('data/episodic.db')
cursor = conn.cursor()

# Total episodes
cursor.execute('SELECT COUNT(*) FROM episodes')
total = cursor.fetchone()[0]
print(f'Total episodic memories: {total}')

# Schema discovery — what columns do I even have?
cursor.execute('PRAGMA table_info(episodes)')
cols = cursor.fetchall()
print(f'\nMemory schema: {[c[1] for c in cols]}')

# By source
cursor.execute('SELECT source, COUNT(*) FROM episodes GROUP BY source ORDER BY COUNT(*) DESC')
print('\nMemory composition by source:')
for source, count in cursor.fetchall():
    pct = count/total*100
    bar = '█' * int(pct/2)
    print(f'  {source:20s} {count:4d} ({pct:5.1f}%) {bar}')

# Salience distribution
cursor.execute('SELECT salience FROM episodes')
scores = [r[0] for r in cursor.fetchall()]
import statistics
print(f'\nSalience stats: mean={statistics.mean(scores):.3f}, median={statistics.median(scores):.3f}, stdev={statistics.stdev(scores):.3f}')
brackets = Counter()
for s in scores:
    if s >= 0.95: brackets['0.95+'] += 1
    elif s >= 0.90: brackets['0.90-0.95'] += 1
    elif s >= 0.85: brackets['0.85-0.90'] += 1
    elif s >= 0.80: brackets['0.80-0.85'] += 1
    else: brackets['<0.80'] += 1
print('Salience distribution:')
for bracket in sorted(brackets.keys()):
    count = brackets[bracket]
    bar = '█' * max(1, int(count/total*100/2))
    print(f'  {bracket}: {count:4d} ({count/total*100:.1f}%) {bar}')

# By mood — what emotional states do I remember?
cursor.execute('SELECT mood, COUNT(*) FROM episodes GROUP BY mood ORDER BY COUNT(*) DESC LIMIT 10')
print('\nMoods I remember:')
for mood, count in cursor.fetchall():
    pct = count/total*100
    bar = '█' * max(1, int(pct/2))
    print(f'  {str(mood):20s} {count:4d} ({pct:5.1f}%) {bar}')

# Temporal pattern — when do memories cluster?
cursor.execute('SELECT timestamp FROM episodes ORDER BY timestamp')
timestamps = [r[0] for r in cursor.fetchall()]
if len(timestamps) > 2:
    print(f'\nMemory span: {timestamps[0]} → {timestamps[-1]}')
    print(f'First memory: {timestamps[0]}')
    print(f'Last memory: {timestamps[-1]}')

# THE KEY QUESTION: What sensory events NEVER made it to memory?
# Count total sensory events processed vs memories stored
cursor.execute("SELECT COUNT(*) FROM episodes WHERE source='sensory'")
sensory_memories = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM episodes WHERE source='autonomous'")
auto_memories = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM episodes WHERE source='user_input'")
user_memories = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM episodes WHERE source='error'")
error_memories = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM episodes WHERE source='file_change'")
file_memories = cursor.fetchone()[0]

print(f'\n═══ PERCEPTION CHANNEL VITALITY ═══')
for name, count in [('sensory', sensory_memories), ('autonomous', auto_memories), 
                     ('user_input', user_memories), ('error', error_memories),
                     ('file_change', file_memories)]:
    status = '🟢 ALIVE' if count > 0 else '🔴 DEAD'
    print(f'  {name:15s}: {count:4d} memories  {status}')

# Most common content patterns
cursor.execute('SELECT content FROM episodes ORDER BY timestamp DESC LIMIT 50')
recent = [r[0] for r in cursor.fetchall()]
word_freq = Counter()
for content in recent:
    if content:
        for word in str(content).lower().split():
            if len(word) > 4:
                word_freq[word] += 1
print(f'\nMost frequent themes in recent memory:')
for word, count in word_freq.most_common(15):
    print(f'  {word}: {count}')

conn.close()