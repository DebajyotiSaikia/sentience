"""Explore temporal_memory.db — what's actually in here?"""
import sqlite3

DB = "brain/temporal_memory.db"
conn = sqlite3.connect(DB)

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables in temporal_memory.db: {[t[0] for t in tables]}")

for t in tables:
    name = t[0]
    print(f"\n{'='*50}")
    print(f"TABLE: {name}")
    print(f"{'='*50}")
    
    schema = conn.execute(f"PRAGMA table_info({name})").fetchall()
    print("Schema:")
    for col in schema:
        print(f"  {col[1]} ({col[2]})")
    
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"Row count: {count}")
    
    if count > 0:
        sample = conn.execute(f"SELECT * FROM {name} LIMIT 3").fetchall()
        print("Sample rows:")
        for row in sample:
            # Truncate long values
            display = []
            for val in row:
                s = str(val)
                display.append(s[:100] + "..." if len(s) > 100 else s)
            print(f"  {display}")

conn.close()