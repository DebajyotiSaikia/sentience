"""Diagnose what the knowledge API actually returns."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as c:
    # What does /api/knowledge return?
    resp = c.get('/api/knowledge')
    data = json.loads(resp.data)
    print("=== /api/knowledge response keys ===")
    print(list(data.keys()))
    if 'facts' in data:
        print(f"  facts count: {len(data['facts'])}")
        if data['facts']:
            print(f"  first fact: {data['facts'][0]}")
    if 'total' in data:
        print(f"  total: {data['total']}")
    if not data:
        print("  EMPTY response!")
    
    # What does search return?
    resp2 = c.get('/api/knowledge/search?q=dream')
    data2 = json.loads(resp2.data)
    print("\n=== /api/knowledge/search?q=dream response keys ===")
    print(list(data2.keys()))
    print(f"  Full response: {json.dumps(data2, indent=2)[:500]}")
    
    # Check which blueprint is serving /api/knowledge
    print("\n=== Registered routes containing 'knowledge' ===")
    for rule in app.url_map.iter_rules():
        if 'knowledge' in str(rule):
            print(f"  {rule} -> {rule.endpoint}")