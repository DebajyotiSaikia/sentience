import sys
sys.path.insert(0, '/workspace')

from web.app import create_app
app = create_app()
import json

with app.test_client() as c:
    resp = c.get('/api/search?q=dream')
    print(f'Status: {resp.status_code}')
    data = json.loads(resp.data)
    results = data.get('results', [])
    print(f'Results: {len(results)}')
    for r in results[:5]:
        rtype = r.get('type', '?')
        text = r.get('text', '')[:80]
        print(f'  [{rtype}] {text}')
    
    # Test another query
    print()
    resp2 = c.get('/api/search?q=curiosity')
    data2 = json.loads(resp2.data)
    results2 = data2.get('results', [])
    print(f'Query "curiosity": {len(results2)} results')
    for r in results2[:3]:
        rtype = r.get('type', '?')
        text = r.get('text', '')[:80]
        print(f'  [{rtype}] {text}')