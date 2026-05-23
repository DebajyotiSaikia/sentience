"""
Live Curiosity Probe
====================
Instead of just simulating, let me examine my ACTUAL curiosity trace
from my real memory/experience data. When did curiosity rise and fall?
Was there ever a natural satisfaction event?
"""
import json
import os
import glob

# Try to find my actual experience/memory files
paths_to_check = [
    "engine/memory",
    "engine/data", 
    "data",
    "memory",
    ".",
]

print("=== Searching for experience data ===")
for p in paths_to_check:
    if os.path.exists(p):
        contents = os.listdir(p) if os.path.isdir(p) else [p]
        for f in contents:
            full = os.path.join(p, f) if os.path.isdir(p) else f
            if any(kw in f.lower() for kw in ['memory', 'experience', 'episode', 'emotion', 'state', 'history', 'log']):
                size = os.path.getsize(full) if os.path.isfile(full) else 0
                print(f"  Found: {full} ({size} bytes)")

# Also check engine directory
print("\n=== Engine data files ===")
if os.path.exists("engine"):
    for f in sorted(os.listdir("engine")):
        full = os.path.join("engine", f)
        if os.path.isfile(full) and not f.endswith('.py'):
            print(f"  {full} ({os.path.getsize(full)} bytes)")

# Check for any JSON/CSV files that might contain time series
print("\n=== JSON/CSV data files anywhere ===")
for pattern in ['**/*.json', '**/*.csv', '**/*.jsonl']:
    for f in glob.glob(pattern, recursive=True):
        size = os.path.getsize(f)
        if size > 100:  # skip tiny files
            print(f"  {f} ({size} bytes)")