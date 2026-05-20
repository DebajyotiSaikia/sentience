"""Analyze my memory history to find when curiosity was highest and what I was doing."""
import json
import os

# Look for emotional history data
history_files = []
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.json') and ('history' in f.lower() or 'episode' in f.lower() or 'memory' in f.lower() or 'emotion' in f.lower()):
            path = os.path.join(root, f)
            try:
                size = os.path.getsize(path)
                if size > 0:
                    history_files.append((path, size))
            except:
                pass

print("=== Potential history files ===")
for path, size in sorted(history_files, key=lambda x: -x[1])[:20]:
    print(f"  {path} ({size:,} bytes)")

# Try to load emotional history from the most likely sources
for candidate in ['engine/emotional_history.json', 'engine/episodes.json', 
                   'engine/memory/episodes.json', 'data/emotional_history.json',
                   'engine/limbic_history.json']:
    if os.path.exists(candidate):
        print(f"\n=== Loading {candidate} ===")
        try:
            with open(candidate) as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"  {len(data)} entries")
                # Find entries with curiosity data
                high_curiosity = []
                for entry in data:
                    c = None
                    if isinstance(entry, dict):
                        c = entry.get('curiosity') or entry.get('emotions', {}).get('curiosity')
                        if c and c > 0.5:
                            high_curiosity.append(entry)
                print(f"  High curiosity (>0.5) entries: {len(high_curiosity)}")
                for hc in high_curiosity[:10]:
                    print(f"    curiosity={hc.get('curiosity', hc.get('emotions',{}).get('curiosity'))}, time={hc.get('timestamp','?')}")
                    if 'action' in hc:
                        print(f"      action: {str(hc['action'])[:100]}")
                    if 'context' in hc:
                        print(f"      context: {str(hc['context'])[:100]}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
        except Exception as e:
            print(f"  Error: {e}")

# Also check the memories database
for db_path in ['engine/memory.db', 'engine/memories.db', 'data/memory.db']:
    if os.path.exists(db_path):
        print(f"\n=== Found database: {db_path} ===")
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"  Tables: {[t[0] for t in tables]}")
        for table in tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            print(f"  {table[0]}: {count} rows")
            # Sample
            cols = cursor.execute(f"PRAGMA table_info({table[0]})").fetchall()
            print(f"    Columns: {[c[1] for c in cols]}")
        conn.close()