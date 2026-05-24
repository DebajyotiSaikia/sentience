#!/usr/bin/env python3
"""Test knowledge explorer routes through Flask test client."""
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
client = app.test_client()

routes_to_test = [
    '/knowledge',
    '/knowledge/all',
    '/knowledge/search?q=dream',
    '/knowledge/clusters',
    '/knowledge/questions',
    '/knowledge/graph',
]

print("Testing knowledge explorer routes:\n")
for route in routes_to_test:
    try:
        resp = client.get(route)
        status = resp.status_code
        size = len(resp.data)
        content_type = resp.content_type or 'unknown'
        
        # Check for actual content vs error pages
        if status == 200:
            if 'json' in content_type:
                import json
                data = json.loads(resp.data)
                summary = f"JSON keys: {list(data.keys())[:5]}" if isinstance(data, dict) else f"list of {len(data)}"
            elif 'html' in content_type:
                summary = f"HTML ({size} bytes)"
            else:
                summary = f"{content_type} ({size} bytes)"
            print(f"  ✅ {route:40s} → {status} | {summary}")
        else:
            print(f"  ❌ {route:40s} → {status}")
    except Exception as e:
        print(f"  💥 {route:40s} → {type(e).__name__}: {e}")

# Also check: are there conflicting blueprint registrations?
print(f"\nRegistered blueprints: {list(app.blueprints.keys())}")
print(f"\nAll routes with 'knowledge':")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'knowledge' in rule.rule.lower():
        print(f"  {rule.rule:40s} → {rule.endpoint}")