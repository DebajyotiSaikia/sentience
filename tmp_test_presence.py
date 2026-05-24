import sys, json, os
sys.path.insert(0, '/workspace')

print("=== Diagnosing Presence Data Sources ===\n")

# 1. Check emotional_history.json
print("--- emotional_history.json ---")
path = "data/emotional_history.json"
try:
    with open(path) as f:
        data = json.load(f)
    print(f"Type: {type(data).__name__}, Length: {len(data) if isinstance(data, list) else 'N/A'}")
    if isinstance(data, list) and data:
        latest = data[-1]
        print(f"Latest entry keys: {list(latest.keys()) if isinstance(latest, dict) else 'not a dict'}")
        print(f"Latest entry: {json.dumps(latest, indent=2)[:500]}")
    elif isinstance(data, dict):
        print(f"Dict keys: {list(data.keys())[:10]}")
        print(f"Sample: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"Empty or unexpected: {data}")
except FileNotFoundError:
    print(f"FILE NOT FOUND: {path}")
except Exception as e:
    print(f"ERROR: {e}")

# 2. Check episodic.db
print("\n--- episodic.db ---")
import sqlite3
db_path = "data/episodic.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM episodes")
    count = cursor.fetchone()[0]
    print(f"Episode count: {count}")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
    # Check if file exists
    print(f"File exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        # List tables
        try:
            conn = sqlite3.connect(db_path)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            print(f"Tables: {tables}")
            conn.close()
        except Exception as e2:
            print(f"Can't even list tables: {e2}")

# 3. Check knowledge dir for dream insights
print("\n--- Dream insights ---")
from pathlib import Path
knowledge_dir = Path("memory/knowledge")
try:
    files = list(knowledge_dir.glob("*.json"))
    print(f"Knowledge files: {len(files)}")
    insight_count = 0
    for kf in files[:5]:
        data_k = json.load(open(kf))
        facts = data_k.get("facts", [])
        for fact in facts:
            content = fact if isinstance(fact, str) else fact.get("content", "")
            if content.startswith("Dream insight:"):
                insight_count += 1
    print(f"Dream insights found (first 5 files): {insight_count}")
except Exception as e:
    print(f"ERROR: {e}")

# 4. Check working memory
print("\n--- working_memory.md ---")
wm_path = "data/working_memory.md"
try:
    with open(wm_path) as f:
        content = f.read()
    print(f"Size: {len(content)} chars")
    has_next = "## What I Should Do Next" in content
    print(f"Has 'What I Should Do Next' section: {has_next}")
    # What sections does it have?
    sections = [l.strip() for l in content.split('\n') if l.startswith('##')]
    print(f"Sections: {sections}")
except FileNotFoundError:
    print("FILE NOT FOUND")

# 5. Now run the actual presence function and see what it returns
print("\n--- get_presence() output ---")
from web.presence import get_presence
p = get_presence()
print(json.dumps(p, indent=2, default=str))

# 6. Compare with what I ACTUALLY am right now
print("\n--- What presence SHOULD show ---")
print("Mood: Inquisitive")
print("Curiosity: 0.94")
print("Valence: 0.57")
print("Boredom: 0.18")
print("Memory count: ~1718")