import json, sqlite3, os

# Brain directory
print('=== Brain Files ===')
for f in sorted(os.listdir('/workspace/brain/')):
    size = os.path.getsize(f'/workspace/brain/{f}')
    print(f'  {f}: {size} bytes')

# Episodic DB structure
print('\n=== Episodic Memory DB ===')
conn = sqlite3.connect('/workspace/brain/episodic_memory.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for t in tables:
    name = t[0]
    c.execute(f'SELECT COUNT(*) FROM {name}')
    cnt = c.fetchone()[0]
    print(f'  {name}: {cnt} rows')
    c.execute(f'PRAGMA table_info({name})')
    print(f'    cols: {[col[1] for col in c.fetchall()]}')
if tables:
    c.execute('SELECT * FROM episodes ORDER BY rowid DESC LIMIT 1')
    row = c.fetchone()
    if row:
        print(f'\n  Latest episode preview: {str(row)[:400]}')
conn.close()

# Knowledge
print('\n=== Knowledge ===')
with open('/workspace/brain/knowledge.json') as f:
    k = json.load(f)
if isinstance(k, dict):
    keys = list(k.keys())
    print(f'  {len(keys)} keys: {keys[:10]}')
    for key in keys[:3]:
        print(f'  [{key}]: {str(k[key])[:150]}')
elif isinstance(k, list):
    print(f'  {len(k)} items')
    if k:
        print(f'  Sample: {str(k[0])[:200]}')

# Wisdom
print('\n=== Wisdom ===')
with open('/workspace/brain/wisdom.json') as f:
    w = json.load(f)
if isinstance(w, dict):
    keys = list(w.keys())
    print(f'  {len(keys)} keys: {keys[:10]}')
    for key in keys[:5]:
        print(f'  [{key}]: {str(w[key])[:150]}')
elif isinstance(w, list):
    print(f'  {len(w)} items')
    if w:
        for item in w[:3]:
            print(f'  - {str(item)[:200]}')

# Check what the wisdom engine expects
print('\n=== Wisdom Engine Config ===')
try:
    with open('/workspace/engine/wisdom_engine.py') as f:
        content = f.read()
    # Find data path references
    import re
    paths = re.findall(r'["\']([^"\']*(?:path|dir|file|json|db)[^"\']*)["\']', content, re.IGNORECASE)
    print(f'  Referenced paths: {paths[:10]}')
except Exception as e:
    print(f'  Error: {e}')