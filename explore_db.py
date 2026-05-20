"""Explore my episodic memory database structure and content."""
import sqlite3
import os

# Check both databases
for db_path in ['./brain/episodic_memory.db', './brain/episodic.db']:
    if not os.path.exists(db_path):
        print(f"[SKIP] {db_path} not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"DATABASE: {db_path}")
    print(f"Size: {os.path.getsize(db_path) / 1024:.1f} KB")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTables: {tables}")
    
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"Columns: {[(c[1], c[2]) for c in columns]}")
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = cursor.fetchall()
            col_names = [c[1] for c in columns]
            for row in rows:
                print(f"  Sample: {dict(zip(col_names, row))}")
    
    conn.close()

print("\n\nDone exploring.")