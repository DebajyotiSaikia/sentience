"""Find duplicate routes across all registered Flask blueprints."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()

# Collect all routes and group by (url_rule, methods)
from collections import defaultdict

rule_map = defaultdict(list)
for rule in app.url_map.iter_rules():
    key = rule.rule
    rule_map[key].append({
        'endpoint': rule.endpoint,
        'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'}),
    })

print("=== DUPLICATE ROUTES ===")
found = 0
for url, entries in sorted(rule_map.items()):
    if len(entries) > 1:
        found += 1
        print(f"\n  URL: {url}")
        for e in entries:
            print(f"    -> {e['endpoint']}  methods={e['methods']}")

if not found:
    print("\n  No duplicates found! All clean.")

print(f"\n=== TOTAL ROUTES: {len(rule_map)} ===")