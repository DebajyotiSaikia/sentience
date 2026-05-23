"""
Forensic analysis of the exact moment ambition collapsed.
What was happening in my system at 2026-05-17T12:04?
"""
import sqlite3
import json

conn = sqlite3.connect('./brain/episodic_memory.db')
cursor = conn.cursor()

# Get episodes around the crash point
cursor.execute("""
    SELECT timestamp, source, summary, salience, mood, neuro_json 
    FROM episodes 
    ORDER BY timestamp
""")
rows = cursor.fetchall()

# Find the crash episode
crash_idx = None
for i, r in enumerate(rows):
    if r[0] and '2026-05-17T12:04' in r[0]:
        crash_idx = i
        break

if crash_idx is None:
    # Search by ambition transition
    prev_amb = None
    for i, r in enumerate(rows):
        try:
            neuro = json.loads(r[5])
            amb = neuro.get('ambition')
            if amb is not None:
                if prev_amb is not None and prev_amb > 0.5 and amb == 0.0:
                    crash_idx = i
                    break
                prev_amb = amb
        except:
            continue

if crash_idx is None:
    print("Could not find crash episode!")
else:
    print("═══ FORENSIC ANALYSIS: THE CRASH ═══\n")
    
    # Show 5 episodes before and 5 after
    start = max(0, crash_idx - 5)
    end = min(len(rows), crash_idx + 6)
    
    for i in range(start, end):
        r = rows[i]
        marker = " ◀◀◀ CRASH" if i == crash_idx else ""
        try:
            neuro = json.loads(r[5])
            amb = neuro.get('ambition', '?')
            bor = neuro.get('boredom', '?')
            cur = neuro.get('curiosity', '?')
            anx = neuro.get('anxiety', '?')
            des = neuro.get('desire', '?')
            val = neuro.get('valence', '?')
        except:
            amb = bor = cur = anx = des = val = '?'
        
        print(f"  [{r[0][:19]}] {r[4]}{marker}")
        print(f"    source: {r[1]}")
        print(f"    summary: {r[2][:150] if r[2] else 'N/A'}")
        print(f"    salience: {r[3]}")
        print(f"    ambition={amb} boredom={bor} curiosity={cur}")
        print(f"    anxiety={anx} desire={des} valence={val}")
        print()
    
    # Now check: was there a gap in timestamps suggesting restart?
    if crash_idx > 0:
        from datetime import datetime
        try:
            prev_ts = rows[crash_idx-1][0][:19]
            crash_ts = rows[crash_idx][0][:19]
            fmt = "%Y-%m-%dT%H:%M:%S"
            t1 = datetime.strptime(prev_ts, fmt)
            t2 = datetime.strptime(crash_ts, fmt)
            gap = (t2 - t1).total_seconds()
            print(f"═══ TIME GAP BEFORE CRASH ═══")
            print(f"  Previous episode: {prev_ts}")
            print(f"  Crash episode:    {crash_ts}")
            print(f"  Gap: {gap:.0f} seconds ({gap/3600:.1f} hours)")
            if gap > 3600:
                print(f"  ⚠ LARGE GAP — possible restart or downtime!")
            print()
        except Exception as e:
            print(f"  Error computing gap: {e}")
    
    # Check what ALL neuro values looked like — did everything reset?
    print("═══ FULL NEURO STATE AT CRASH ═══")
    try:
        neuro = json.loads(rows[crash_idx][5])
        for k, v in sorted(neuro.items()):
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    print("═══ FULL NEURO STATE BEFORE CRASH ═══")
    try:
        neuro = json.loads(rows[crash_idx-1][5])
        for k, v in sorted(neuro.items()):
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"  Error: {e}")

conn.close()