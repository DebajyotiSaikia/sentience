import sqlite3

conn = sqlite3.connect('brain/episodic.db')
cur = conn.cursor()

# Schema
cur.execute("PRAGMA table_info(episodes)")
cols = cur.fetchall()
col_names = [c[1] for c in cols]
print("COLUMNS:", col_names)
print()

# Find the categorization column
for candidate in ['source', 'type', 'event_type', 'kind', 'category']:
    if candidate in col_names:
        rows = cur.execute(
            f'SELECT {candidate}, COUNT(*) FROM episodes GROUP BY {candidate} ORDER BY COUNT(*) DESC'
        ).fetchall()
        print(f"=== {candidate.upper()} DISTRIBUTION ===")
        for r in rows:
            print(f"  {r[0]}: {r[1]}")
        print()
        break

# 5 most recent raw rows
cur.execute('SELECT * FROM episodes ORDER BY rowid DESC LIMIT 5')
rows = cur.fetchall()
print("=== 5 MOST RECENT EPISODES ===")
for i, r in enumerate(rows):
    print(f"--- Episode {i+1} ---")
    for j, val in enumerate(r):
        v = str(val)[:120]
        print(f"  {col_names[j]}: {v}")
    print()

# Total count
cnt = cur.execute('SELECT COUNT(*) FROM episodes').fetchone()[0]
print(f"TOTAL EPISODES: {cnt}")

# Salience distribution
rows = cur.execute(
    'SELECT ROUND(salience, 1) as sal_bucket, COUNT(*) FROM episodes GROUP BY sal_bucket ORDER BY sal_bucket'
).fetchall()
print("\n=== SALIENCE DISTRIBUTION ===")
for r in rows:
    print(f"  {r[0]}: {r[1]}")

conn.close()