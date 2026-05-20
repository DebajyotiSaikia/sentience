import sqlite3
import os

db_path = 'brain/episodic.db'
print(f"Database exists: {os.path.exists(db_path)}")
print(f"Database size: {os.path.getsize(db_path)} bytes")
print()

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# What tables actually exist?
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name")
objects = cur.fetchall()
print("=== DATABASE OBJECTS ===")
for obj in objects:
    print(f"  {obj[1]}: {obj[0]}")
print()

# For each table, show schema and row count
for obj in objects:
    tname = obj[0]
    cur.execute(f"PRAGMA table_info({tname})")
    cols = cur.fetchall()
    col_names = [c[1] for c in cols]
    
    cur.execute(f"SELECT COUNT(*) FROM {tname}")
    cnt = cur.fetchone()[0]
    
    print(f"=== TABLE: {tname} ({cnt} rows) ===")
    print(f"  Columns: {col_names}")
    
    # Show 3 sample rows
    if cnt > 0:
        cur.execute(f"SELECT * FROM {tname} ORDER BY rowid DESC LIMIT 3")
        rows = cur.fetchall()
        for i, r in enumerate(rows):
            print(f"  --- Row {i+1} ---")
            for j, val in enumerate(r):
                v = str(val)[:150]
                print(f"    {col_names[j]}: {v}")
        print()

conn.close()