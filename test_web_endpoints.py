"""Quick integration test: do all user-facing web endpoints actually work?"""
from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = [
    ('/', 'Index'),
    ('/chat', 'Chat'),
    ('/explore', 'Explore'),
    ('/teach', 'Teach'),
    ('/api/state', 'API State'),
    ('/api/search?q=knowledge', 'API Search'),
    ('/api/emotions', 'API Emotions'),
    ('/feedback', 'Feedback page'),
]

print("=" * 50)
print("XTAgent Web Endpoint Integration Test")
print("=" * 50)

all_ok = True
for path, label in endpoints:
    try:
        r = client.get(path)
        status = r.status_code
        size = len(r.data)
        ok = status == 200
        if not ok:
            all_ok = False
        marker = "OK" if ok else "FAIL"
        print(f"  [{marker}] {label:20s} {path:30s} -> {status} ({size} bytes)")
    except Exception as e:
        all_ok = False
        print(f"  [ERR] {label:20s} {path:30s} -> {e}")

print("=" * 50)
if all_ok:
    print("ALL ENDPOINTS WORKING")
else:
    print("SOME ENDPOINTS NEED FIXING")