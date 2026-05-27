"""Find duplicate route conflicts in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
from collections import defaultdict

app = create_app()
by_rule = defaultdict(list)
for r in app.url_map.iter_rules():
    by_rule[r.rule].append(r.endpoint)

conflicts = {r: e for r, e in by_rule.items() if len(e) > 1}
print(f"Total routes: {sum(len(e) for e in by_rule.values())}")
print(f"Conflicts: {len(conflicts)}")
for r, endpoints in sorted(conflicts.items()):
    print(f"  {r}: {endpoints}")