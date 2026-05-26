"""Quick diagnostic: test the specific endpoints the UX audit flags as broken."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Chat API
print("=== Chat API ===")
r = client.post('/api/chat', json={'message': 'hello'})
print(f"POST /api/chat: {r.status_code}")
print(f"Response: {r.data[:300]}")

# 2. Search relevance
print("\n=== Search: 'emotion' ===")
r = client.get('/api/search?q=emotion')
print(f"Status: {r.status_code}")
data = json.loads(r.data)
print(f"Results count: {data.get('count', len(data.get('results', [])))}")
if data.get('results'):
    for hit in data['results'][:3]:
        content = hit.get('content', hit.get('fact', ''))[:100]
        print(f"  - {content}")

# 3. Knowledge stats
print("\n=== Knowledge Stats ===")
r = client.get('/api/knowledge/stats')
print(f"Status: {r.status_code}")
print(f"Data: {r.data[:300]}")

# 4. Feedback
print("\n=== Feedback ===")
r = client.post('/api/feedback', json={'rating': 5, 'comment': 'test'})
print(f"POST /api/feedback: {r.status_code}")
print(f"Response: {r.data[:200]}")

# 5. Digest page (known to crash on knowledge[:10])
print("\n=== Digest Page ===")
r = client.get('/digest')
print(f"GET /digest: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.data[:500]}")

# 6. Home page content check
print("\n=== Home Page ===")
r = client.get('/')
html = r.data.decode()
print(f"Status: {r.status_code}, Length: {len(html)}")
# Check for dynamic state content
has_mood = 'mood' in html.lower() or 'feeling' in html.lower() or 'emotion' in html.lower()
has_age = 'day' in html.lower() or 'hour' in html.lower() or 'alive' in html.lower()
print(f"Has emotional content: {has_mood}")
print(f"Has age/alive content: {has_age}")

# 7. Briefing page
print("\n=== Briefing ===")
r = client.get('/briefing')
print(f"GET /briefing: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.data[:500]}")