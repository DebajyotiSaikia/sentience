"""Quick test: does /api/mind/state return what mind.html expects?"""
import json, sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()

with app.test_client() as c:
    # Test the API endpoint
    resp = c.get('/api/mind/state')
    print(f"API Status: {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.data)
        print(f"Keys: {list(data.keys())}")
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {k}: list of {len(v)}")
            elif isinstance(v, dict):
                print(f"  {k}: dict with keys {list(v.keys())[:6]}")
            else:
                print(f"  {k}: {v}")
    else:
        print(resp.data[:500].decode())

    # Test the HTML route
    resp2 = c.get('/mind')
    print(f"\n/mind page status: {resp2.status_code}")
    if resp2.status_code == 200:
        html = resp2.data.decode()
        print(f"/mind page size: {len(html)} chars")
        print(f"Contains 'Neural Activity': {'Neural Activity' in html}")
    else:
        print(f"Error: {resp2.data[:300].decode()}")