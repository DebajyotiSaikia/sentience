import sqlite3, json, os

# Check episodic database
db_path = 'data/episodic.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"=== Episodic DB tables: {[t[0] for t in tables]} ===")
    for t in tables:
        name = t[0]
        cur.execute(f'PRAGMA table_info({name})')
        cols = cur.fetchall()
        print(f"\n{name} columns: {[c[1] for c in cols]}")
        cur.execute(f'SELECT COUNT(*) FROM {name}')
        print(f"  count: {cur.fetchone()[0]}")
        cur.execute(f'SELECT * FROM {name} LIMIT 1')
        row = cur.fetchone()
        if row:
            print(f"  sample: {str(row)[:400]}")
    conn.close()
else:
    print(f"{db_path} does not exist")

# Check what search.py currently tries to load
print("\n=== File existence check ===")
for p in ['data/knowledge.json', 'brain/knowledge.json', 'data/memories.json',
          'persist/memories.json', 'brain/memories.json', 'data/episodic.db']:
    print(f"  {p}: {'EXISTS' if os.path.exists(p) else 'missing'}")

# Show search.py's load functions
print("\n=== search.py data loading ===")
with open('web/search.py') as f:
    content = f.read()
    # Find load/read functions
    for i, line in enumerate(content.split('\n')):
        if any(kw in line.lower() for kw in ['load', 'open(', 'json', 'path', 'data/', 'brain/', 'persist/']):
            print(f"  L{i+1}: {line.strip()}")