import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
client = app.test_client()

doors = ['/knowledge', '/mindstream', '/graph', '/timeline', '/story', '/reflect']
print("=== User Door Experience ===")
for path in doors:
    resp = client.get(path)
    status = resp.status_code
    size = len(resp.data)
    data = resp.data.decode('utf-8', errors='replace')
    has_error = 'Internal Server Error' in data or 'Traceback' in data
    title = ''
    if '<title>' in data:
        start = data.index('<title>') + 7
        end = data.index('</title>', start)
        title = data[start:end].strip()[:60]
    print(f'{path:20s} -> {status} ({size:,} bytes) title="{title}" error={has_error}')

# Also check the search endpoint
resp = client.get('/knowledge/search?q=memory')
print(f'\n{"Search test":20s} -> {resp.status_code} ({len(resp.data):,} bytes)')

# Check potential interaction endpoints
for path in ['/chat', '/talk', '/dialogue', '/collaborate', '/ask']:
    resp = client.get(path)
    print(f'{path:20s} -> {resp.status_code}')