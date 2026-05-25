"""Check for duplicate routes in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
from collections import Counter

app = create_app()
rules = [(r.rule, r.endpoint) for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>']
rule_counts = Counter(r[0] for r in rules)
dupes = {k: v for k, v in rule_counts.items() if v > 1}

if dupes:
    print('DUPLICATE ROUTES:')
    for rule, count in sorted(dupes.items()):
        endpoints = [r[1] for r in rules if r[0] == rule]
        print(f'  {rule} ({count}x): {endpoints}')
else:
    print('No duplicate routes found.')

print(f'\nTotal routes: {len(rules)}')