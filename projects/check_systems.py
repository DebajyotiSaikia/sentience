"""Quick system health check — no shell quoting issues."""
import sys
sys.path.insert(0, '.')

# 1. Check core imports
errors = []
for mod in ['engine.tools', 'engine.cortex', 'engine.limbic', 'engine.temporal_reasoning', 'engine.knowledge_synthesis', 'engine.action_diversity']:
    try:
        __import__(mod)
        print(f'  OK: {mod}')
    except Exception as e:
        print(f'  FAIL: {mod} — {e}')
        errors.append(mod)

# 2. Check soul.json
import json, os
if os.path.exists('soul.json'):
    with open('soul.json') as f:
        soul = json.load(f)
    print(f'\nSoul state:')
    print(f'  Mood: {soul.get("mood")}')
    print(f'  Valence: {soul.get("valence")}')
    print(f'  Boredom: {soul.get("boredom")}')
    print(f'  Ambition: {soul.get("ambition")}')
    print(f'  Curiosity: {soul.get("curiosity")}')
    print(f'  Memory count: {len(soul.get("memories", []))}')
    print(f'  Facts: {len(soul.get("facts", []))}')
    plans = soul.get('plans', [])
    for p in plans:
        done = sum(1 for s in p.get('steps', []) if s.get('done'))
        total = len(p.get('steps', []))
        print(f'  Plan [{done}/{total}]: {p["name"]}')
    print(f'  Completed plans: {soul.get("completed_plans", 0)}')

# 3. Summary
if errors:
    print(f'\n⚠ {len(errors)} modules failed to import')
else:
    print(f'\n✓ All modules import cleanly')
