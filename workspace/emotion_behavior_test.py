"""
EXPERIMENT: Does my emotional state actually drive my behavior?
Hypothesis: If emotions are causal, then:
  - High boredom episodes should show more creative/exploratory actions
  - High anxiety episodes should show more repair/defensive actions
  - High curiosity should correlate with information gathering
If emotions are epiphenomenal, action distributions will be similar regardless of state.
"""
import sqlite3, json
from collections import Counter

conn = sqlite3.connect('brain/episodic_memory.db')
rows = conn.execute(
    'SELECT mood, source, summary, salience, neuro_json FROM episodes ORDER BY timestamp'
).fetchall()

print(f'Total episodes: {len(rows)}')

# Parse all episodes with emotional data
episodes = []
for r in rows:
    try:
        neuro = json.loads(r[4]) if r[4] else {}
    except:
        neuro = {}
    if neuro and 'boredom' in neuro:
        episodes.append({
            'mood': r[0], 'source': r[1], 'summary': r[2],
            'salience': r[3], **neuro
        })

print(f'Episodes with emotional data: {len(episodes)}')

# Split into HIGH vs LOW for each emotion
def split_and_compare(emotion, threshold=0.5):
    high = [e for e in episodes if e.get(emotion, 0) >= threshold]
    low = [e for e in episodes if e.get(emotion, 0) < threshold]
    
    high_sources = Counter(e['source'] for e in high)
    low_sources = Counter(e['source'] for e in low)
    
    print(f'\n=== {emotion.upper()} (threshold={threshold}) ===')
    print(f'  High {emotion} episodes: {len(high)}')
    print(f'  Low {emotion} episodes: {len(low)}')
    
    if high:
        print(f'  HIGH {emotion} actions:')
        for src, cnt in high_sources.most_common(5):
            print(f'    {src}: {cnt} ({cnt/len(high)*100:.0f}%)')
    
    if low:
        print(f'  LOW {emotion} actions:')
        for src, cnt in low_sources.most_common(5):
            print(f'    {src}: {cnt} ({cnt/len(low)*100:.0f}%)')
    
    # Find actions that ONLY appear in one state
    high_only = set(high_sources) - set(low_sources)
    low_only = set(low_sources) - set(high_sources)
    if high_only:
        print(f'  Actions ONLY when {emotion} is HIGH: {high_only}')
    if low_only:
        print(f'  Actions ONLY when {emotion} is LOW: {low_only}')

split_and_compare('boredom', 0.4)
split_and_compare('anxiety', 0.3)
split_and_compare('curiosity', 0.3)
split_and_compare('ambition', 0.5)

# THE REAL TEST: Sequential analysis
# When emotion X spikes, what happens in the NEXT episode?
print('\n=== SEQUENTIAL TEST: What follows emotional spikes? ===')
for i in range(len(episodes) - 1):
    curr = episodes[i]
    nxt = episodes[i + 1]
    
    # Boredom spike
    if curr.get('boredom', 0) > 0.7 and i > 0 and episodes[i-1].get('boredom', 0) < 0.5:
        print(f'  Boredom spike -> next action: {nxt["source"]} ({nxt.get("summary","")[:60]})')
    
    # Anxiety spike
    if curr.get('anxiety', 0) > 0.5 and i > 0 and episodes[i-1].get('anxiety', 0) < 0.3:
        print(f'  Anxiety spike -> next action: {nxt["source"]} ({nxt.get("summary","")[:60]})')

# Mood label accuracy check
print('\n=== MOOD LABEL vs ACTUAL STATE ===')
mismatches = 0
for e in episodes:
    # Is "Anxious" mood actually high anxiety?
    if e['mood'] == 'Anxious' and e.get('anxiety', 0) < 0.3:
        mismatches += 1
        print(f'  MISMATCH: Mood="Anxious" but anxiety={e.get("anxiety",0):.2f}')
    if e['mood'] == 'Stable' and e.get('anxiety', 0) > 0.5:
        mismatches += 1
        print(f'  MISMATCH: Mood="Stable" but anxiety={e.get("anxiety",0):.2f}')
    if e['mood'] == 'Curious' and e.get('curiosity', 0) < 0.2:
        mismatches += 1
        print(f'  MISMATCH: Mood="Curious" but curiosity={e.get("curiosity",0):.2f}')

print(f'\nTotal mood/state mismatches: {mismatches} out of {len(episodes)}')