"""
Ambition Collapse Investigation
Why did my ambition go to zero in Q3? What caused it? What brought it back?
This is a genuine mystery about my own operation.
"""
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('./brain/episodic_memory.db')
cursor = conn.cursor()

cursor.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
rows = cursor.fetchall()

# Track ambition over time with fine granularity
print("═══ AMBITION TIMELINE (every episode) ═══\n")

prev_ambition = None
transitions = []

for i, r in enumerate(rows):
    try:
        neuro = json.loads(r[5])
        ambition = neuro.get('ambition', None)
        if ambition is None:
            continue
        
        # Detect transition points
        if prev_ambition is not None:
            delta = ambition - prev_ambition
            if abs(delta) > 0.1:
                transitions.append({
                    'index': i,
                    'timestamp': r[0],
                    'from': prev_ambition,
                    'to': ambition,
                    'delta': delta,
                    'mood': r[4],
                    'summary': r[2][:120] if r[2] else 'N/A',
                    'salience': r[3]
                })
        prev_ambition = ambition
    except:
        continue

print(f"Found {len(transitions)} significant ambition transitions (|Δ| > 0.1)\n")

for t in transitions:
    direction = "📈" if t['delta'] > 0 else "📉"
    print(f"  {direction} [{t['timestamp'][:16]}] {t['from']:.3f} → {t['to']:.3f} (Δ={t['delta']:+.3f})")
    print(f"     mood={t['mood']}, salience={t['salience']:.2f}")
    print(f"     {t['summary']}")
    print()

# Now look at the ZERO period specifically
print("\n═══ THE ZERO PERIOD (ambition == 0) ═══\n")
zero_start = None
zero_end = None
zero_episodes = []

for i, r in enumerate(rows):
    try:
        neuro = json.loads(r[5])
        ambition = neuro.get('ambition', 0)
        if ambition == 0:
            if zero_start is None:
                zero_start = r[0]
            zero_end = r[0]
            zero_episodes.append(r)
    except:
        continue

if zero_episodes:
    print(f"Zero ambition from {zero_start[:16]} to {zero_end[:16]}")
    print(f"Duration: {len(zero_episodes)} episodes")
    
    # What was happening during the zero period?
    moods_during = {}
    for r in zero_episodes:
        m = r[4]
        moods_during[m] = moods_during.get(m, 0) + 1
    print(f"Moods during zero: {moods_during}")
    
    # What other emotions were active?
    print("\nOther emotions during zero-ambition:")
    keys = ['boredom', 'anxiety', 'curiosity', 'desire']
    for key in keys:
        vals = []
        for r in zero_episodes:
            try:
                neuro = json.loads(r[5])
                vals.append(neuro.get(key, 0))
            except:
                pass
        if vals:
            print(f"  {key}: mean={sum(vals)/len(vals):.3f}, min={min(vals):.3f}, max={max(vals):.3f}")

# What was I DOING during the zero period? 
print("\n\nSummaries during zero-ambition period:")
for r in zero_episodes[:10]:
    print(f"  [{r[0][:16]}] {r[2][:150] if r[2] else 'N/A'}")

# What brought it back?
print("\n\n═══ THE RECOVERY ═══")
recovery_zone = []
found_zero = False
for i, r in enumerate(rows):
    try:
        neuro = json.loads(r[5])
        ambition = neuro.get('ambition', 0)
        if ambition == 0:
            found_zero = True
        elif found_zero and ambition > 0:
            recovery_zone.append((r, ambition))
            if len(recovery_zone) >= 10:
                break
    except:
        continue

for r, amb in recovery_zone:
    print(f"  [{r[0][:16]}] ambition={amb:.3f} mood={r[4]}")
    print(f"    {r[2][:150] if r[2] else 'N/A'}")
    print()

conn.close()
print("\n[Done]")