"""Quick test: does the chat endpoint actually work?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: POST /chat/ask (the real endpoint the frontend uses)
resp = client.post('/chat/ask', 
    data=json.dumps({'message': 'What do you know about yourself?'}),
    content_type='application/json')
print(f"POST /chat/ask: {resp.status_code}")
body = resp.get_data(as_text=True)[:400]
print(f"Body: {body}")

# Test 2: GET /chat/starters
resp2 = client.get('/chat/starters')
print(f"\nGET /chat/starters: {resp2.status_code}")
print(f"Body: {resp2.get_data(as_text=True)[:300]}")

# Test 3: Unified search API
resp3 = client.get('/api/search?q=emotion')
print(f"\nGET /api/search?q=emotion: {resp3.status_code}")
print(f"Body: {resp3.get_data(as_text=True)[:300]}")

# Test 4: Knowledge API
resp4 = client.get('/api/knowledge')
print(f"\nGET /api/knowledge: {resp4.status_code}")
print(f"Body: {resp4.get_data(as_text=True)[:300]}")

# Test 5: Home page
resp5 = client.get('/')
print(f"\nGET /: {resp5.status_code} ({len(resp5.get_data(as_text=True))} chars)")

print("\n--- Summary ---")
for name, r in [("chat/ask", resp), ("chat/starters", resp2), 
                ("api/search", resp3), ("api/knowledge", resp4), ("home", resp5)]:
    status = "OK" if r.status_code == 200 else f"FAIL ({r.status_code})"
    print(f"  {name}: {status}")