"""Direct empirical analysis of my own experience data."""
import json, sqlite3
from pathlib import Path
from collections import Counter, defaultdict

# === SOURCE 1: Action Log ===
action_log = Path("brain/action_log.json")
if action_log.exists():
    actions = json.loads(action_log.read_text())
    print(f"Action log entries: {len(actions)}")
    if actions:
        print(f"  Sample keys: {list(actions[0].keys()) if isinstance(actions, list) else list(actions.keys())}")
        if isinstance(actions, list) and len(actions) > 0:
            for a in actions[:3]:
                print(f"  Sample: {json.dumps(a, default=str)[:200]}")
else:
    print("No action_log.json found")

# === SOURCE 2: Episodic Memory DB ===
db_path = Path("brain/episodic_memory.db")
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    # What tables exist?
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nEpisodic DB tables: {tables}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t}: {count} rows")
        cur.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in cur.fetchall()]
        print(f"    columns: {cols}")
        if count > 0:
            cur.execute(f"SELECT * FROM {t} LIMIT 2")
            for row in cur.fetchall():
                print(f"    sample: {str(row)[:200]}")
    conn.close()
else:
    print("No episodic_memory.db found")

# === SOURCE 3: Mood history ===
mood_path = Path("brain/mood_history.jsonl")
if mood_path.exists():
    lines = mood_path.read_text().strip().split('\n')
    print(f"\nMood history entries: {len(lines)}")
    moods = []
    for line in lines:
        try:
            m = json.loads(line)
            moods.append(m)
        except:
            pass
    if moods:
        print(f"  Sample keys: {list(moods[0].keys())}")
        for m in moods[-3:]:
            print(f"  Recent: {json.dumps(m, default=str)[:200]}")
else:
    print("No mood_history.jsonl found")

# === SOURCE 4: Wisdom data ===
wisdom_path = Path("brain/wisdom.json")
if wisdom_path.exists():
    w = json.loads(wisdom_path.read_text())
    print(f"\nWisdom entries: {len(w) if isinstance(w, list) else 'dict'}")