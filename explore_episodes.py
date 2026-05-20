import sqlite3

conn = sqlite3.connect('data/episodic.db')
cursor = conn.cursor()

# What tables exist?
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    name = t[0]
    print(f"\n{'='*60}")
    print(f"TABLE: {name}")
    print('='*60)
    
    # Schema
    cursor.execute(f"PRAGMA table_info({name})")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"Columns: {cols}")
    
    # Count
    cursor.execute(f"SELECT COUNT(*) FROM {name}")
    print(f"Rows: {cursor.fetchone()[0]}")
    
    # Sample
    cursor.execute(f"SELECT * FROM {name} LIMIT 3")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()