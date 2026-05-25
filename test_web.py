"""Quick test of web endpoints to find real bugs."""
from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = [
    '/', '/chat', '/explore', '/teach',
    '/api/search?q=knowledge', '/api/plans', '/health',
    '/api/state', '/api/knowledge/random',
    '/api/feedback', '/api/teach/submissions',
    '/dashboard',
]

print("=== Web Endpoint Test ===\n")
for ep in endpoints:
    try:
        resp = client.get(ep)
        status = resp.status_code
        size = len(resp.data)
        ok = '\u2713' if status == 200 else '\u2717'
        print(f'  {ok} {ep:40s} -> {status} ({size:>6} bytes)')
    except Exception as e:
        print(f'  \u2717 {ep:40s} -> ERROR: {e}')

print("\n=== Route Map ===\n")
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for r in rules:
    print(f'  {r.rule:45s} -> {r.endpoint:30s} {list(r.methods - {"HEAD","OPTIONS"})}')