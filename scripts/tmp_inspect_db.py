import sqlite3, os

for db_path in ['brain/episodic.db', 'brain/episodic_memory.db', 'brain/memory.db', 'brain/temporal_memory.db']:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"--- {db_path} ---")
        for t in tables:
            tname = t[0]
            cols = conn.execute(f"PRAGMA table_info({tname})").fetchall()
            count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            col_names = [c[1] for c in cols]
            print(f"  {tname} ({count} rows): {col_names}")
            if count > 0 and count <= 3:
                rows = conn.execute(f"SELECT * FROM {tname} LIMIT 2").fetchall()
                for r in rows:
                    print(f"    sample: {r[:3]}...")
        conn.close()
    else:
        print(f"--- {db_path} --- NOT FOUND")