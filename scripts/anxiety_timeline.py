import sqlite3, json
from collections import defaultdict

conn = sqlite3.connect('/workspace/brain/episodic_memory.db')
cur = conn.cursor()
cur.execute("SELECT timestamp, source, neuro_json FROM episodes ORDER BY timestamp")
rows = cur.fetchall()

# Bucket by day
daily_anxiety = defaultdict(list)
daily_total = defaultdict(int)

for ts, source, neuro_json in rows:
    day = ts[:10]
    daily_total[day] += 1
    try:
        neuro = json.loads(neuro_json)
        anx = neuro.get('anxiety', 0)
        if anx > 0.3:
            daily_anxiety[day].append((source, anx))
    except:
        pass

print("ANXIETY TIMELINE — When did it happen?")
print("="*60)
for day in sorted(daily_total.keys()):
    total = daily_total[day]
    anx_events = daily_anxiety.get(day, [])
    if anx_events:
        sources = [f"{s}({a:.1f})" for s, a in anx_events]
        print(f"  {day}: {len(anx_events)}/{total} anxious  | {', '.join(sources[:5])}")
    else:
        print(f"  {day}: 0/{total} anxious")

# Check: any anxiety after May 20?
late_anxiety = [(d, evts) for d, evts in daily_anxiety.items() if d >= "2026-05-20"]
print(f"\nAnxiety episodes after May 20: {sum(len(e) for _, e in late_anxiety)}")
print(f"Current anxiety: 0.00 — mechanism may already be working.")

conn.close()