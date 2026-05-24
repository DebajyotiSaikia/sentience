"""Verify knowledge routes are clean — no duplicates after cleanup."""
from app import create_app

app = create_app()
routes = sorted(set(r.rule for r in app.url_map.iter_rules() if 'knowledge' in r.rule))
for r in routes:
    print(r)
print(f'\n{len(routes)} knowledge routes total')

# Check for duplicates
all_rules = [r.rule for r in app.url_map.iter_rules() if 'knowledge' in r.rule]
from collections import Counter
dupes = {k: v for k, v in Counter(all_rules).items() if v > 1}
if dupes:
    print(f'\n⚠ DUPLICATES FOUND:')
    for route, count in dupes.items():
        print(f'  {route} registered {count} times')
else:
    print('\n✓ No duplicate routes.')