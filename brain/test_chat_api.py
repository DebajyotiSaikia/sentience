"""Quick diagnostic: what exactly does POST /api/chat return?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: POST /api/chat with JSON
print("=== Test 1: POST /api/chat (JSON) ===")
resp = client.post('/api/chat', json={'message': 'Hello'}, content_type='application/json')
print(f"Status: {resp.status_code}")
print(f"Data: {resp.data[:500]}")

# Test 2: POST /api/chat with form data
print("\n=== Test 2: POST /api/chat (form) ===")
resp2 = client.post('/api/chat', data={'message': 'Hello'})
print(f"Status: {resp2.status_code}")
print(f"Data: {resp2.data[:500]}")

# Test 3: Feedback endpoint
print("\n=== Test 3: POST /api/feedback ===")
resp3 = client.post('/api/feedback', json={'rating': 5, 'comment': 'test'}, content_type='application/json')
print(f"Status: {resp3.status_code}")
print(f"Data: {resp3.data[:500]}")

# Test 4: Knowledge stats
print("\n=== Test 4: GET /api/knowledge/stats ===")
resp4 = client.get('/api/knowledge/stats')
print(f"Status: {resp4.status_code}")
print(f"Data: {resp4.data[:500]}")

# Test 5: Search
print("\n=== Test 5: GET /api/search?q=emotion ===")
resp5 = client.get('/api/search?q=emotion')
print(f"Status: {resp5.status_code}")
print(f"Data: {resp5.data[:500]}")