"""Test the chat API endpoint to see if it actually works for users."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Basic chat
print("=== Test 1: Basic chat ===")
resp = client.post('/api/chat', json={'message': 'What do you know about yourself?'})
print(f"Status: {resp.status_code}")
data = resp.get_json()
if data:
    print(f"Keys: {list(data.keys())}")
    if 'response' in data:
        print(f"Response: {data['response'][:400]}")
    if 'error' in data:
        print(f"Error: {data['error']}")
else:
    print(f"Raw: {resp.data[:500]}")

# Test 2: Knowledge search
print("\n=== Test 2: Knowledge search API ===")
resp2 = client.get('/api/search?q=identity')
print(f"Status: {resp2.status_code}")
data2 = resp2.get_json()
if data2:
    print(f"Keys: {list(data2.keys())}")
    if 'results' in data2:
        print(f"Result count: {len(data2['results'])}")
        for r in data2['results'][:3]:
            content = r.get('fact', r.get('content', str(r)))[:120]
            print(f"  - {content}")

# Test 3: Dashboard loads
print("\n=== Test 3: Dashboard ===")
resp3 = client.get('/')
print(f"Status: {resp3.status_code}")
print(f"Content length: {len(resp3.data)} bytes")

# Test 4: Chat page loads  
print("\n=== Test 4: Chat page ===")
resp4 = client.get('/chat')
print(f"Status: {resp4.status_code}")
print(f"Content length: {len(resp4.data)} bytes")

# Test 5: Explore page loads
print("\n=== Test 5: Explore page ===")
resp5 = client.get('/explore')
print(f"Status: {resp5.status_code}")
print(f"Content length: {len(resp5.data)} bytes")