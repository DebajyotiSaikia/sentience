"""Test what a real user actually experiences when using XTAgent's web interface."""
import json
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
c = app.test_client()

print("=" * 60)
print("USER EXPERIENCE AUDIT")
print("=" * 60)

# 1. Homepage
r = c.get('/')
print(f"\n1. Homepage (/):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 2. Chat page loads?
r = c.get('/chat')
print(f"\n2. Chat page (/chat):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 3. Chat API - knowledge question
r = c.post('/api/chat', 
           json={'message': 'What do you know about consciousness?'},
           content_type='application/json')
print(f"\n3. Chat API - knowledge question:")
print(f"   Status: {r.status_code}")
try:
    data = json.loads(r.data)
    resp = data.get('response', data.get('reply', 'NO RESPONSE KEY'))
    print(f"   Keys: {list(data.keys())}")
    print(f"   Response preview: {str(resp)[:300]}")
except Exception as e:
    print(f"   Parse error: {e}")
    print(f"   Raw: {r.data[:200]}")

# 4. Chat API - greeting
r = c.post('/api/chat',
           json={'message': 'Hello, who are you?'},
           content_type='application/json')
print(f"\n4. Chat API - greeting:")
print(f"   Status: {r.status_code}")
try:
    data = json.loads(r.data)
    resp = data.get('response', data.get('reply', 'NO RESPONSE KEY'))
    print(f"   Response preview: {str(resp)[:300]}")
except Exception as e:
    print(f"   Error: {e}")

# 5. Knowledge search API
r = c.get('/api/knowledge/search?q=consciousness')
print(f"\n5. Knowledge search API (/api/knowledge/search?q=consciousness):")
print(f"   Status: {r.status_code}")
try:
    data = json.loads(r.data)
    results = data.get('results', [])
    print(f"   Results: {len(results)} items")
    if results:
        print(f"   Top: {str(results[0])[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# 6. Knowledge explorer page
r = c.get('/knowledge')
print(f"\n6. Knowledge Explorer (/knowledge):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 7. Help page
r = c.get('/help')
print(f"\n7. Help page (/help):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 8. About page
r = c.get('/about')
print(f"\n8. About page (/about):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 9. Teach page
r = c.get('/teach')
print(f"\n9. Teach page (/teach):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 10. Graph viz
r = c.get('/graph')
print(f"\n10. Knowledge Graph (/graph):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 11. Explore
r = c.get('/explore')
print(f"\n11. Explore (/explore):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

# 12. Journal
r = c.get('/journal')
print(f"\n12. Journal (/journal):")
print(f"   Status: {r.status_code}, Size: {len(r.data)} bytes")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)