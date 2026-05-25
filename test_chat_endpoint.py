"""Quick test: verify chat endpoint works end-to-end."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test chat ask endpoint
resp = client.post('/chat/ask', json={'message': 'What do you know about yourself?'})
print(f'Chat ask status: {resp.status_code}')
data = resp.get_json()
if data:
    print(f'Response keys: {list(data.keys())}')
    if 'response' in data:
        print(f'Response preview: {data["response"][:200]}')
    if 'error' in data:
        print(f'Error: {data["error"]}')
else:
    print(f'Raw response: {resp.data[:500]}')

# Test chat suggestions endpoint (if exists)
resp2 = client.get('/chat/suggestions')
print(f'\nSuggestions status: {resp2.status_code}')
if resp2.status_code == 200:
    print(f'Suggestions: {resp2.get_json()}')

# Test state API
resp3 = client.get('/api/state')
print(f'\nState API status: {resp3.status_code}')
if resp3.status_code == 200:
    state = resp3.get_json()
    print(f'State keys: {list(state.keys())}')