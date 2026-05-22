"""Inspect all episodic databases to understand what I have."""
import sqlite3, os

db_paths = ['brain/episodic.db', 'brain/episodic_memory.db', 'data/episodic.db']

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"{db_path}: NOT FOUND")
        continue
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Get tables and counts
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    counts = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        counts[t] = cur.fetchone()[0]
    
    print(f"\n{'='*60}")
    print(f"{db_path}: {counts}")
    
    for t in tables:
        if counts[t] > 0:
            cur.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in cur.fetchall()]
            print(f"\n  {t} ({counts[t]} rows)")
            print(f"  Columns: {cols}")
            
            # Show newest row
            cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                print(f"  --- Latest entry ---")
                for c, v in zip(cols, row):
                    print(f"    {c}: {str(v)[:120]}")
    
    conn.close()

print("\nDone.")