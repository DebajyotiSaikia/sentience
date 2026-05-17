"""Check arena status — what's solved, what remains."""
import json, os, sys
sys.path.insert(0, '/workspace/arena')

# Load results
solved_ids = set()
if os.path.exists('results.json'):
    data = json.load(open('results.json'))
    for r in data:
        if r.get('solved'):
            solved_ids.add(r['challenge_id'])
    print(f"Total solved: {len(solved_ids)}")
    for r in data:
        if r.get('solved'):
            print(f"  ✓ Level {r['level']}: {r['challenge_id']}")
else:
    print("No results yet")

# Show remaining
from challenge_engine import CHALLENGES
remaining = [c for c in CHALLENGES if c['id'] not in solved_ids]
print(f"\nRemaining: {len(remaining)} challenges")
for c in remaining:
    print(f"  Level {c['level']}: {c['title']} ({c['id']})")
    if 'description' in c:
        print(f"    {c['description'][:80]}")