"""List all registered Flask routes related to chat and feedback."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

print("=== ALL ROUTES ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:8s} {rule.rule}")

print("\n=== CHAT & FEEDBACK ROUTES ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'chat' in rule.rule or 'feedback' in rule.rule:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {methods:8s} {rule.rule}")