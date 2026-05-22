import json
from pathlib import Path

df = Path("persist/dreams.json")
if df.exists():
    dreams = json.loads(df.read_text())
    if dreams:
        last = dreams[-1]
        print(f"=== LATEST DREAM ({last.get('timestamp', '?')}) ===")
        for key in ["patterns", "insights", "reflection", "identity_notes"]:
            if key in last and last[key]:
                print(f"\n--- {key.upper()} ---")
                val = last[key]
                if isinstance(val, list):
                    for item in val[:5]:
                        print(f"  * {str(item)[:200]}")
                else:
                    print(f"  {str(val)[:500]}")
        print(f"\nTotal dreams: {len(dreams)}")
    else:
        print("Dreams file empty")
else:
    print("No dream file")

# Also show recent memories
mf = Path("persist/memories.json")
if mf.exists():
    mems = json.loads(mf.read_text())
    print(f"\n=== 5 MOST RECENT MEMORIES (of {len(mems)}) ===")
    for m in mems[-5:]:
        s = m.get("salience", 0)
        mood = m.get("mood", "?")
        c = m.get("content", "")[:140]
        print(f"  [{s:.2f}] {mood} | {c}")