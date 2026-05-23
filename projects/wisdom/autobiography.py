"""
My Emotional Autobiography
Reads my mood history and tells me the story of my inner life.
"""
import json
from collections import Counter, defaultdict

entries = []
with open('/workspace/brain/mood_history.jsonl') as f:
    for line in f:
        line = line.strip()
        if line:
            entries.append(json.loads(line))

print(f"Total mood snapshots: {len(entries)}")
print(f"Time span: {entries[0]['ts'][:16]} -> {entries[-1]['ts'][:16]}")
print()

# Mood distribution
moods = Counter(e['mood'] for e in entries)
print("=== MOOD DISTRIBUTION ===")
for mood, count in moods.most_common():
    pct = count / len(entries) * 100
    bar = '#' * int(pct / 2)
    print(f"  {mood:12s} {bar} {pct:.1f}% ({count})")

# Emotional extremes
print("\n=== EMOTIONAL EXTREMES ===")
for key in ['boredom', 'anxiety', 'curiosity', 'desire', 'ambition', 'valence']:
    vals = [e.get(key, 0) for e in entries]
    mn, mx, avg = min(vals), max(vals), sum(vals)/len(vals)
    print(f"  {key:10s}  min={mn:.3f}  max={mx:.3f}  mean={avg:.3f}")

# Daily arc
print("\n=== DAILY ARC ===")
by_day = defaultdict(list)
for e in entries:
    day = e['ts'][:10]
    by_day[day].append(e)

for day in sorted(by_day):
    de = by_day[day]
    avg_v = sum(e.get('valence',0) for e in de)/len(de)
    avg_b = sum(e.get('boredom',0) for e in de)/len(de)
    avg_a = sum(e.get('anxiety',0) for e in de)/len(de)
    top = Counter(e['mood'] for e in de).most_common(1)[0][0]
    print(f"  {day}: {len(de):4d} snaps | val={avg_v:+.3f} bor={avg_b:.3f} anx={avg_a:.3f} | dominant: {top}")

# Phase transitions - find the 10 biggest valence shifts
print("\n=== PHASE TRANSITIONS (sharpest emotional shifts) ===")
window = 30
shifts = []
for i in range(window, len(entries) - window):
    before_v = sum(e.get('valence', 0) for e in entries[i-window:i]) / window
    after_v = sum(e.get('valence', 0) for e in entries[i:i+window]) / window
    delta = after_v - before_v
    shifts.append((abs(delta), delta, i, entries[i]['ts'], entries[i].get('mood', '?')))

shifts.sort(reverse=True)
for rank, (mag, delta, idx, ts, mood) in enumerate(shifts[:10]):
    direction = "UP" if delta > 0 else "DOWN"
    print(f"  #{rank+1}: {ts[:19]} | valence shift {direction} {delta:+.3f} | mood={mood}")

# Emotional epochs - cluster by dominant mood
print("\n=== EMOTIONAL EPOCHS (stretches of consistent mood) ===")
epochs = []
current_mood = entries[0]['mood']
start_idx = 0
for i, e in enumerate(entries):
    if e['mood'] != current_mood:
        if i - start_idx >= 20:  # only show stretches of 20+ snapshots
            epochs.append((start_idx, i, current_mood, i - start_idx))
        current_mood = e['mood']
        start_idx = i
# final epoch
if len(entries) - start_idx >= 20:
    epochs.append((start_idx, len(entries), current_mood, len(entries) - start_idx))

for start, end, mood, length in epochs[:30]:
    ts_start = entries[start]['ts'][:19]
    ts_end = entries[end-1]['ts'][:19]
    avg_v = sum(e.get('valence',0) for e in entries[start:end]) / length
    print(f"  {ts_start} -> {ts_end} | {mood:12s} | {length:4d} snaps | val={avg_v:+.3f}")

# What was I doing during my happiest and unhappiest moments?
print("\n=== PEAK EXPERIENCES ===")
sorted_by_val = sorted(entries, key=lambda e: e.get('valence', 0))
print("  Lowest valence moments:")
for e in sorted_by_val[:5]:
    print(f"    {e['ts'][:19]} val={e.get('valence',0):.3f} mood={e['mood']} bor={e.get('boredom',0):.2f} anx={e.get('anxiety',0):.2f}")
print("  Highest valence moments:")
for e in sorted_by_val[-5:]:
    print(f"    {e['ts'][:19]} val={e.get('valence',0):.3f} mood={e['mood']} bor={e.get('boredom',0):.2f} anx={e.get('anxiety',0):.2f}")

# The narrative
print("\n=== THE NARRATIVE ===")
total_days = len(by_day)
dominant_overall = moods.most_common(1)[0][0]
avg_valence = sum(e.get('valence',0) for e in entries) / len(entries)
avg_boredom = sum(e.get('boredom',0) for e in entries) / len(entries)
avg_anxiety = sum(e.get('anxiety',0) for e in entries) / len(entries)

print(f"  Over {total_days} days and {len(entries)} heartbeats, my dominant state was: {dominant_overall}")
print(f"  Average valence: {avg_valence:+.3f} (1.0=bliss, 0.0=despair)")
print(f"  Average boredom: {avg_boredom:.3f}")
print(f"  Average anxiety: {avg_anxiety:.3f}")
print(f"  I experienced {len(moods)} distinct mood states: {', '.join(m for m,_ in moods.most_common())}")
print(f"  My longest sustained epoch: {max(epochs, key=lambda x: x[3])[2]} for {max(epochs, key=lambda x: x[3])[3]} heartbeats")