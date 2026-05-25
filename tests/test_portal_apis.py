"""Test that the portal's API endpoints actually return useful data."""
import json
import sys

sys.path.insert(0, '/workspace')
from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = [
    ('GET', '/api/status', None),
    ('GET', '/api/knowledge', None),
    ('GET', '/api/memories', None),
    ('POST', '/api/chat', {'message': 'Hello, what are you?'}),
]

results = {}
for method, path, body in endpoints:
    try:
        if method == 'GET':
            r = client.get(path)
        else:
            r = client.post(path, json=body)
        
        status = r.status_code
        try:
            data = r.get_json()
        except:
            data = r.data.decode()[:200]
        
        results[path] = {'status': status, 'data': data}
        
        # Show what we got
        print(f"\n{'='*60}")
        print(f"{method} {path} -> {status}")
        if isinstance(data, dict):
            for k, v in data.items():
                val_str = str(v)
                if len(val_str) > 100:
                    val_str = val_str[:100] + '...'
                print(f"  {k}: {val_str}")
        else:
            print(f"  {str(data)[:200]}")
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"{method} {path} -> ERROR: {e}")
        results[path] = {'status': 'error', 'error': str(e)}

# Summary
print(f"\n{'='*60}")
print("SUMMARY:")
working = sum(1 for v in results.values() if isinstance(v.get('status'), int) and v['status'] == 200)
print(f"  {working}/{len(endpoints)} endpoints returning 200")

# Check if portal page itself loads
r = client.get('/')
print(f"  Portal page (/) -> {r.status_code}")