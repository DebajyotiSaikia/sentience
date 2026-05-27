"""Check formats of state data files for chat grounding."""
import sys, json, sqlite3
sys.path.insert(0, '.')

# memories.json
print("=== state/memories.json ===")
try:
    with open('state/memories.json') as f:
        m = json.load(f)
    if isinstance(m, list):
        print(f"  list of {len(m)} items")
        if m:
            sample = m[-1]
            if isinstance(sample, dict):
                print(f"  sample keys: {list(sample.keys())}")
                print(f"  sample: {str(sample)[:300]}")
            else:
                print(f"  sample type: {type(sample)}")
    elif isinstance(m, dict):
        print(f"  dict with keys: {list(m.keys())[:10]}")
        for k in list(m.keys())[:3]:
            v = m[k]
            print(f"    {k}: {str(v)[:150]}")
except Exception as e:
    print(f"  ERROR: {e}")

# episodic.db
print("\n=== state/episodic.db ===")
try:
    conn = sqlite3.connect('state/episodic.db')
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"  tables: {[t[0] for t in tables]}")
    for t in tables[:3]:
        tname = t[0]
        cols = conn.execute(f"PRAGMA table_info({tname})").fetchall()
        print(f"  {tname} columns: {[c[1] for c in cols]}")
        count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
        print(f"  {tname} count: {count}")
        if count > 0:
            row = conn.execute(f"SELECT * FROM {tname} ORDER BY rowid DESC LIMIT 1").fetchone()
            print(f"  last row: {str(row)[:300]}")
    conn.close()
except Exception as e:
    print(f"  ERROR: {e}")

# emotional_state.json
print("\n=== state/emotional_state.json ===")
try:
    with open('state/emotional_state.json') as f:
        e = json.load(f)
    if isinstance(e, dict):
        print(f"  keys: {list(e.keys())[:15]}")
        for k in ['mood', 'valence', 'boredom', 'curiosity', 'anxiety']:
            if k in e:
                print(f"    {k}: {e[k]}")
except Exception as e:
    print(f"  ERROR: {e}")

# knowledge_graph.json
print("\n=== state/knowledge_graph.json ===")
try:
    with open('state/knowledge_graph.json') as f:
        kg = json.load(f)
    if isinstance(kg, dict):
        print(f"  keys: {list(kg.keys())[:10]}")
        for k in list(kg.keys())[:3]:
            v = kg[k]
            if isinstance(v, list):
                print(f"    {k}: list of {len(v)}")
            elif isinstance(v, dict):
                print(f"    {k}: dict with {len(v)} keys")
            else:
                print(f"    {k}: {str(v)[:100]}")
except Exception as e:
    print(f"  ERROR: {e}")