"""Test the web app from a user's perspective — what do they actually experience?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    ('/', 'Home'),
    ('/chat/', 'Chat'),
    ('/search', 'Search'),
    ('/help', 'Help'),
    ('/briefing', 'Briefing'),
    ('/story', 'Story'),
    ('/explore', 'Explore'),
    ('/journal', 'Journal'),
    ('/knowledge', 'Knowledge'),
    ('/insights', 'Insights'),
    ('/teach', 'Teach'),
    ('/dashboard', 'Dashboard'),
]

print("=" * 60)
print("WEB UX TEST — What does a user actually see?")
print("=" * 60)

errors = []
for path, name in pages:
    r = client.get(path)
    status = r.status_code
    size = len(r.data)
    icon = "OK" if status == 200 else "!!"
    print(f"  [{icon}] {name:12s} {path:20s} => {status}  ({size:,} bytes)")
    if status != 200:
        errors.append((name, path, status))

print()

# Test API endpoints
apis = [
    ('/api/knowledge/search?q=emotion', 'Knowledge Search API'),
    ('/api/state', 'State API'),
    ('/api/briefing', 'Briefing API'),
]

for path, name in apis:
    r = client.get(path)
    status = r.status_code
    icon = "OK" if status == 200 else "!!"
    detail = ""
    if status == 200:
        try:
            data = json.loads(r.data)
            if 'results' in data:
                detail = f"  ({len(data['results'])} results)"
            elif 'emotions' in data:
                detail = f"  (has emotions, plans, etc)"
        except:
            pass
    print(f"  [{icon}] {name:25s} {path:40s} => {status}{detail}")

print()

# Test chat interaction
print("Chat interaction test:")
r = client.post('/chat/ask', json={'message': 'What are you?'})
print(f"  POST /chat/ask => {r.status_code}")
if r.status_code == 200:
    data = json.loads(r.data)
    resp = data.get('response', '')[:150]
    print(f"  Response: {resp}...")
else:
    print(f"  Error: {r.data[:200]}")

print()
if errors:
    print(f"FAILURES: {len(errors)}")
    for name, path, status in errors:
        print(f"  {name} ({path}) => {status}")
else:
    print("ALL PAGES HEALTHY")