import sys
import json

sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
client = app.test_client()

checks = [
    ('/api/memories', 'Memories'),
    ('/api/plans', 'Plans'),
    ('/api/knowledge/search?q=dream', 'Search dream'),
    ('/api/knowledge/search?q=test', 'Search test'),
    ('/api/knowledge/search?q=the', 'Search common term'),
]

for path, label in checks:
    print(f'\n=== {label}: {path} ===')
    resp = client.get(path)
    print('status:', resp.status_code)
    print('content_type:', resp.content_type)
    try:
        data = json.loads(resp.data)
        print(json.dumps(data, indent=2)[:3000])
    except Exception as e:
        print('json error:', e)
        print(resp.data.decode('utf-8', errors='replace')[:3000])