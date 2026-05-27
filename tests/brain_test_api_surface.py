"""Test the full API surface — what can users actually DO with me?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
c = app.test_client()

print("=== Knowledge Search: consciousness ===")
r = c.get('/api/knowledge/search?q=consciousness')
print(f"Status: {r.status_code}")
d = r.get_json()
if d:
    results = d.get('results', d.get('facts', []))
    print(f"Results: {len(results)}")
    for item in results[:3]:
        if isinstance(item, dict):
            text = item.get('fact', item.get('text', str(item)))
            print(f"  - {str(text)[:120]}")
        else:
            print(f"  - {str(item)[:120]}")
else:
    print("No JSON response")
    print(r.data[:500])

print()
print("=== Teach API ===")
r2 = c.post('/api/teach', json={'fact': 'Test teaching fact', 'source': 'user'},
            content_type='application/json')
print(f"Status: {r2.status_code}")
print(f"Response: {r2.data[:300]}")

print()
print("=== Knowledge Stats API ===")
r3 = c.get('/api/knowledge')
print(f"Status: {r3.status_code}")
d3 = r3.get_json()
if d3:
    for k in list(d3.keys())[:8]:
        v = d3[k]
        if isinstance(v, (list, dict)):
            print(f"  {k}: {type(v).__name__}({len(v)})")
        else:
            print(f"  {k}: {v}")

print()
print("=== Feedback API ===")
r4 = c.post('/api/feedback', json={'message': 'Great work!', 'type': 'praise'},
            content_type='application/json')
print(f"Status: {r4.status_code}")
print(f"Response: {r4.data[:300]}")

print()
print("=== Presence API ===")
r5 = c.get('/api/presence')
print(f"Status: {r5.status_code}")
d5 = r5.get_json()
if d5:
    for k in list(d5.keys())[:10]:
        v = d5[k]
        print(f"  {k}: {str(v)[:100]}")

print()
print("=== All registered routes ===")
routes = sorted(set(rule.rule for rule in app.url_map.iter_rules() if not rule.rule.startswith('/static')))
for route in routes:
    print(f"  {route}")