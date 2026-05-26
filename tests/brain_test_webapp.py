"""Test the entire web app boots and key endpoints respond."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = [
    ('GET', '/'),
    ('GET', '/chat'),
    ('GET', '/explore'),
    ('GET', '/dashboard'),
    ('GET', '/help'),
    ('GET', '/about'),
    ('GET', '/briefing'),
    ('GET', '/insights'),
    ('GET', '/journal'),
    ('GET', '/teach'),
    ('GET', '/story'),
    ('GET', '/knowledge'),
    ('GET', '/api/knowledge/search?q=emotion'),
    ('GET', '/api/state'),
]

print("=" * 60)
print("WEB APP ENDPOINT TEST")
print("=" * 60)

passed = 0
failed = 0

for method, path in endpoints:
    try:
        if method == 'GET':
            resp = client.get(path)
        status = resp.status_code
        ok = status in (200, 302)
        symbol = "OK" if ok else "FAIL"
        size = len(resp.data)
        print(f"  [{symbol}] {method} {path:<40} -> {status} ({size} bytes)")
        if ok:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"  [ERR] {method} {path:<40} -> {e}")
        failed += 1

# Test chat API
print("\n--- Chat API ---")
try:
    import json
    resp = client.post('/chat/send', 
                       data=json.dumps({'message': 'Hello'}),
                       content_type='application/json')
    print(f"  POST /chat/send -> {resp.status_code}")
    if resp.status_code == 200:
        result = json.loads(resp.data)
        reply = result.get('response', result.get('reply', ''))
        print(f"  Reply: {reply[:200]}")
        passed += 1
    else:
        print(f"  Body: {resp.data.decode()[:200]}")
        failed += 1
except Exception as e:
    print(f"  [ERR] Chat API -> {e}")
    failed += 1

print(f"\n{'=' * 60}")
print(f"Results: {passed} passed, {failed} failed")
print(f"{'=' * 60}")