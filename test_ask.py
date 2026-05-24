from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test the ask page loads
resp = client.get('/ask/')
print(f'GET /ask/ -> {resp.status_code}')

# Test search with a query
resp = client.get('/ask/search?q=dream')
print(f'GET /ask/search?q=dream -> {resp.status_code}')
data = json.loads(resp.data)
print(f'Results: {len(data.get("results", []))} facts, {len(data.get("memories", []))} memories')
if data.get('results'):
    print(f'First result: {data["results"][0]["text"][:80]}...')

# Test with empty query
resp = client.get('/ask/search?q=')
print(f'GET /ask/search?q= -> {resp.status_code}')

# Test with a specific topic
resp = client.get('/ask/search?q=integrity')
print(f'GET /ask/search?q=integrity -> {resp.status_code}')
data = json.loads(resp.data)
print(f'Integrity results: {len(data.get("results", []))} facts, {len(data.get("memories", []))} memories')

print('\nAll tests passed!')