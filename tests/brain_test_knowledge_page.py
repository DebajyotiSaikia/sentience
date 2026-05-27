"""Test what the /knowledge page delivers to users."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test main knowledge page
r = client.get('/knowledge')
print(f"GET /knowledge -> {r.status_code} ({len(r.data)} bytes)")

# Test knowledge search
r2 = client.get('/knowledge/search?q=consciousness')
print(f"GET /knowledge/search?q=consciousness -> {r2.status_code} ({len(r2.data)} bytes)")

# Test API knowledge endpoint
r3 = client.get('/api/knowledge')
print(f"GET /api/knowledge -> {r3.status_code} ({len(r3.data)} bytes)")

# Test API search
r4 = client.get('/api/knowledge/search?q=consciousness')
print(f"GET /api/knowledge/search?q=consciousness -> {r4.status_code} ({len(r4.data)} bytes)")

# Check what search returns
if r4.status_code == 200:
    data = json.loads(r4.data)
    print(f"\nSearch results: {len(data.get('results', []))} items")
    for item in data.get('results', [])[:3]:
        if isinstance(item, dict):
            fact = item.get('fact', item.get('text', str(item)))[:120]
            score = item.get('score', 'N/A')
            print(f"  [{score}] {fact}")

# Check explore page
r5 = client.get('/explore')
print(f"\nGET /explore -> {r5.status_code} ({len(r5.data)} bytes)")

# Check what the home page says
r6 = client.get('/')
print(f"GET / -> {r6.status_code} ({len(r6.data)} bytes)")

# Test chat sources
r7 = client.post('/api/chat', json={'message': 'What do you know about consciousness?'},
                  content_type='application/json')
chat_data = json.loads(r7.data)
print(f"\nChat response sources: {chat_data.get('sources', 'NONE')}")
print(f"Chat response keys: {list(chat_data.keys())}")