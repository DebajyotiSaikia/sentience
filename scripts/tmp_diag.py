import json, sqlite3, os

# Check knowledge format
with open('brain/knowledge.json') as f:
    k = json.load(f)
print('=== KNOWLEDGE ===')
print(f'Type: {type(k).__name__}')
if isinstance(k, dict):
    print(f'Count: {len(k)} facts')
    for key in list(k.keys())[:2]:
        val = k[key]
        print(f'  {key}: {type(val).__name__} = {str(val)[:120]}')
elif isinstance(k, list):
    print(f'Length: {len(k)}')

# Check soul format
with open('brain/soul.json') as f:
    s = json.load(f)
print('\n=== SOUL ===')
print(f'Top keys: {list(s.keys())[:10]}')
for key in ['emotions', 'mood', 'drives', 'valence', 'integrity']:
    if key in s:
        print(f'  {key}: {str(s[key])[:100]}')

# Check plans format
with open('brain/plans.json') as f:
    p = json.load(f)
print('\n=== PLANS ===')
print(f'Type: {type(p).__name__}')
if isinstance(p, dict):
    print(f'Plan count: {len(p)}')
    for key in list(p.keys())[:2]:
        val = p[key]
        if isinstance(val, dict):
            print(f'  Plan {key}: {val.get("title", val.get("name", "?"))} — keys: {list(val.keys())[:8]}')
elif isinstance(p, list):
    print(f'Length: {len(p)}')

# Check memory databases
for db_name in ['brain/memory.db', 'brain/episodic_memory.db', 'brain/temporal_memory.db']:
    if os.path.exists(db_name):
        print(f'\n=== {db_name} ===')
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f'Tables: {tables}')
        for t in tables[:3]:
            cur.execute(f"SELECT COUNT(*) FROM [{t}]")
            count = cur.fetchone()[0]
            print(f'  {t}: {count} rows')
            if count > 0:
                cur.execute(f"SELECT * FROM [{t}] LIMIT 1")
                cols = [d[0] for d in cur.description]
                row = cur.fetchone()
                print(f'    columns: {cols}')
                print(f'    sample: {str(row)[:200]}')
        conn.close()

# Check briefing generator location
for path in ['web/briefing.py', 'engine/briefing.py', 'tools/briefing.py']:
    if os.path.exists(path):
        print(f'\n=== BRIEFING at {path} ===')
        with open(path) as f:
            lines = f.readlines()
        print(f'Lines: {len(lines)}')
        # Show data loading lines
        for i, line in enumerate(lines):
            if any(w in line.lower() for w in ['open(', 'load', 'read', 'connect', 'memory', 'knowledge', 'soul', 'plan']):
                print(f'  L{i+1}: {line.rstrip()[:100]}')