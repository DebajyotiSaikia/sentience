import sys, json
sys.path.insert(0, '/workspace')
from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = [
    ('/', 'Homepage'),
    ('/api/status', 'Status API'),
    ('/api/pulse', 'Pulse API'),
    ('/api/facts', 'Facts API'),
    ('/api/memories', 'Memories API'),
    ('/api/plans', 'Plans API'),
    ('/api/knowledge/stats', 'Knowledge Stats'),
    ('/api/knowledge/search?q=dream', 'Knowledge Search'),
    ('/api/graph', 'Graph API'),
    ('/portal', 'Portal page'),
    ('/dashboard', 'Dashboard page'),
    ('/about-me', 'About Me page'),
]

for path, name in endpoints:
    try:
        resp = client.get(path)
        status = resp.status_code
        size = len(resp.data)
        # Check if JSON response has useful content
        snippet = ''
        if resp.content_type and 'json' in resp.content_type:
            try:
                data = json.loads(resp.data)
                if isinstance(data, dict):
                    snippet = f' keys={list(data.keys())[:5]}'
                elif isinstance(data, list):
                    snippet = f' items={len(data)}'
            except:
                pass
        icon = '✓' if status == 200 else '✗'
        print(f'  {icon} [{status}] {name:20s} {path:35s} ({size:>6} bytes){snippet}')
    except Exception as e:
        print(f'  ✗ ERROR {name:20s} {path:35s} {e}')