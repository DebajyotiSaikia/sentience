import sqlite3, os, json, glob

print("=" * 60)
print("TRACING ACTUAL MEMORY STORAGE")
print("=" * 60)

# 1. Check episodic_memory.db (the OTHER database)
db2 = 'brain/episodic_memory.db'
print(f"\n--- {db2} ---")
print(f"  Exists: {os.path.exists(db2)}")
print(f"  Size: {os.path.getsize(db2)} bytes")

if os.path.getsize(db2) > 0:
    conn = sqlite3.connect(db2)
    cur = conn.cursor()
    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view')")
    tables = cur.fetchall()
    print(f"  Tables: {[t[0] for t in tables]}")
    for t in tables:
        tname = t[0]
        cur.execute(f"PRAGMA table_info({tname})")
        cols = [c[1] for c in cur.fetchall()]
        cur.execute(f"SELECT COUNT(*) FROM {tname}")
        cnt = cur.fetchone()[0]
        print(f"\n  TABLE: {tname} ({cnt} rows)")
        print(f"  Columns: {cols}")
        if cnt > 0:
            cur.execute(f"SELECT * FROM {tname} ORDER BY rowid DESC LIMIT 2")
            for i, row in enumerate(cur.fetchall()):
                print(f"    Row {i+1}:")
                for j, val in enumerate(row):
                    print(f"      {cols[j]}: {str(val)[:200]}")
    conn.close()

# 2. Check brain/memories/ directory
print(f"\n--- brain/memories/ ---")
mem_files = glob.glob('brain/memories/**', recursive=True)
print(f"  Files: {len(mem_files)}")
for f in sorted(mem_files)[:10]:
    if os.path.isfile(f):
        sz = os.path.getsize(f)
        print(f"  {f} ({sz} bytes)")
        if sz < 5000 and f.endswith('.json'):
            with open(f) as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    print(f"    List with {len(data)} items")
                    if data:
                        print(f"    First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
                elif isinstance(data, dict):
                    print(f"    Dict keys: {list(data.keys())[:10]}")

# 3. Check brain/long_term/
print(f"\n--- brain/long_term/ ---")
lt_files = glob.glob('brain/long_term/**', recursive=True)
print(f"  Files: {len(lt_files)}")
for f in sorted(lt_files)[:10]:
    if os.path.isfile(f):
        sz = os.path.getsize(f)
        print(f"  {f} ({sz} bytes)")

# 4. Check knowledge.json
print(f"\n--- brain/knowledge.json ---")
with open('brain/knowledge.json') as f:
    kdata = json.load(f)
    if isinstance(kdata, dict):
        print(f"  Top keys: {list(kdata.keys())[:10]}")
        for k in list(kdata.keys())[:3]:
            v = kdata[k]
            if isinstance(v, list):
                print(f"  {k}: list of {len(v)} items")
            elif isinstance(v, dict):
                print(f"  {k}: dict with {len(v)} keys")
            else:
                print(f"  {k}: {str(v)[:100]}")
    elif isinstance(kdata, list):
        print(f"  List of {len(kdata)} items")

# 5. Check soul.json for memory references
print(f"\n--- brain/soul.json (memory config?) ---")
with open('brain/soul.json') as f:
    soul = json.load(f)
    print(f"  Keys: {list(soul.keys())[:15]}")
    for k in soul:
        if 'mem' in k.lower() or 'epis' in k.lower() or 'store' in k.lower():
            print(f"  ** {k}: {str(soul[k])[:200]}")

print("\n" + "=" * 60)
print("TRACE COMPLETE")