"""Test the chat endpoint to see if users can actually talk to me."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test the chat page loads
resp = client.get('/chat/')
print(f'Chat page: {resp.status_code}, {len(resp.data)} bytes')

# Test asking a question
resp = client.post('/chat/ask', 
    data=json.dumps({'message': 'What do you know about yourself?'}),
    content_type='application/json')
print(f'Chat ask: {resp.status_code}')
data = resp.get_json()
if data:
    print(f'Response keys: {list(data.keys())}')
    if 'response' in data:
        print(f'Response (first 500 chars): {data["response"][:500]}')
    if 'error' in data:
        print(f'Error: {data["error"]}')
else:
    print(f'Raw: {resp.data[:500]}')

# Test search endpoint
resp = client.get('/search/api?q=identity')
print(f'\nSearch API: {resp.status_code}')
data = resp.get_json()
if data:
    print(f'Search keys: {list(data.keys())}')
    if 'results' in data:
        print(f'Results count: {len(data["results"])}')
        for r in data['results'][:3]:
            content = r.get('content', r.get('fact', str(r)))[:100]
            print(f'  - {content}')

# Test explore page
resp = client.get('/explore')
print(f'\nExplore page: {resp.status_code}, {len(resp.data)} bytes')

# Test feedback endpoint
resp = client.get('/feedback/summary')
print(f'Feedback summary: {resp.status_code}')

print('\n--- User-facing endpoints summary ---')
user_routes = [r for r in app.url_map.iter_rules() 
               if r.rule.startswith(('/chat', '/search', '/explore', '/feedback', '/graph'))]
for r in sorted(user_routes, key=lambda r: r.rule):
    methods = ','.join(r.methods - {'HEAD', 'OPTIONS'})
    print(f'  {r.rule} [{methods}]')