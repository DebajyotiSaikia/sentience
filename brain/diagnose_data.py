"""Diagnose where memories and knowledge actually live."""
import sqlite3
import json
import os

print("=== SQLite databases ===")
for db_path in ['brain/episodic.db', 'brain/episodic_memory.db', 'data/episodic.db', 'brain/memory.db']:
    if not os.path.exists(db_path):
        print(f"{db_path}: DOES NOT EXIST")
        continue
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if not tables:
            print(f"{db_path}: NO TABLES")
            conn.close()
            continue
        counts = {}
        for t in tables[:5]:
            counts[t] = c.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
        print(f"{db_path}: {counts}")
        # Show schema of biggest table
        biggest = max(counts, key=counts.get)
        cols = [r[1] for r in c.execute(f'PRAGMA table_info([{biggest}])').fetchall()]
        print(f"  Schema of [{biggest}]: {cols}")
        row = c.execute(f'SELECT * FROM [{biggest}] LIMIT 1').fetchone()
        print(f"  Sample: {str(row)[:300]}")
        conn.close()
    except Exception as e:
        print(f"{db_path}: ERROR {e}")

print("\n=== Knowledge JSON ===")
kpath = 'brain/knowledge.json'
if os.path.exists(kpath):
    with open(kpath) as f:
        d = json.load(f)
    print(f"Type: {type(d)}, Top keys: {list(d.keys())[:5]}")
    if 'nodes' in d:
        nodes = d['nodes']
        print(f"  nodes type: {type(nodes)}, count: {len(nodes)}")
        if isinstance(nodes, dict):
            first_key = list(nodes.keys())[0]
            print(f"  Sample node key: {first_key}")
            print(f"  Sample node val: {nodes[first_key]}")
        elif isinstance(nodes, list):
            print(f"  Sample node: {nodes[0]}")
    if 'edges' in d:
        print(f"  edges count: {len(d['edges'])}")
        if d['edges']:
            print(f"  Sample edge: {d['edges'][0]}")