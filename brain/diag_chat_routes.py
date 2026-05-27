"""Diagnose: what chat routes are actually registered?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

print("=== ALL REGISTERED ROUTES ===")
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for r in rules:
    methods = sorted(r.methods - {'OPTIONS', 'HEAD'})
    print(f"  {r.rule:40s} {methods}")

print("\n=== CHAT-RELATED ROUTES ===")
for r in rules:
    if 'chat' in r.rule.lower():
        methods = sorted(r.methods - {'OPTIONS', 'HEAD'})
        print(f"  {r.rule:40s} {methods} -> {r.endpoint}")

print("\n=== API ROUTES ===")
for r in rules:
    if 'api' in r.rule.lower():
        methods = sorted(r.methods - {'OPTIONS', 'HEAD'})
        print(f"  {r.rule:40s} {methods} -> {r.endpoint}")

print("\n=== TESTING CHAT POST ===")
client = app.test_client()

# Try various chat endpoints
for url in ['/chat', '/api/chat', '/chat/', '/api/chat/']:
    for method in ['GET', 'POST']:
        if method == 'GET':
            resp = client.get(url)
        else:
            resp = client.post(url, json={'message': 'hello'}, content_type='application/json')
        print(f"  {method:4s} {url:20s} -> {resp.status_code}")