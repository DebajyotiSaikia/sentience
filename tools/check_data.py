#!/usr/bin/env python3
"""Check what data sources actually exist and their format."""
import os, json, sqlite3, glob

print("=== brain/*.json ===")
for f in sorted(glob.glob("brain/*.json")):
    try:
        d = json.load(open(f))
        if isinstance(d, dict):
            print(f"  {f}: dict with {len(d)} keys, sample keys: {list(d.keys())[:3]}")
        elif isinstance(d, list):
            print(f"  {f}: list with {len(d)} items")
        else:
            print(f"  {f}: {type(d).__name__}")
    except Exception as e:
        print(f"  {f}: ERROR {e}")

print("\n=== brain/*.db ===")
for f in sorted(glob.glob("brain/*.db")):
    try:
        c = sqlite3.connect(f)
        tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in tables:
            count = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            cols = [col[1] for col in c.execute(f"PRAGMA table_info([{t}])").fetchall()]
            print(f"  {f} -> {t}: {count} rows, cols={cols}")
        if not tables:
            print(f"  {f}: NO TABLES")
        c.close()
    except Exception as e:
        print(f"  {f}: ERROR {e}")

print("\n=== brain/memories/ ===")
mem_dir = "brain/memories"
if os.path.isdir(mem_dir):
    files = os.listdir(mem_dir)
    print(f"  {len(files)} files")
    for f in sorted(files)[:3]:
        path = os.path.join(mem_dir, f)
        try:
            d = json.load(open(path))
            if isinstance(d, dict):
                print(f"    {f}: keys={list(d.keys())[:5]}")
            elif isinstance(d, list):
                print(f"    {f}: list len={len(d)}")
        except:
            print(f"    {f}: not JSON")
else:
    print("  NOT FOUND")

print("\n=== persist/*.json ===")
for f in sorted(glob.glob("persist/*.json")):
    try:
        d = json.load(open(f))
        if isinstance(d, dict):
            print(f"  {f}: dict with {len(d)} keys, sample: {list(d.keys())[:3]}")
        elif isinstance(d, list):
            print(f"  {f}: list with {len(d)} items")
    except Exception as e:
        print(f"  {f}: ERROR {e}")