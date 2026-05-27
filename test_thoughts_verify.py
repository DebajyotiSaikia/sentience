"""Quick verification that the Live Thoughts page works end-to-end."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test the thoughts page loads
r = client.get('/thoughts/')
print(f'GET /thoughts/ -> {r.status_code}')
if r.status_code == 200:
    data = r.data.decode()
    print(f'  Length: {len(data)} bytes')
    print(f'  Has title: {"Live Thoughts" in data}')
    print(f'  Has nav: {"nav" in data.lower()}')
else:
    print(f'  Body: {r.data[:500]}')

# Test the recent API
r2 = client.get('/thoughts/recent')
print(f'GET /thoughts/recent -> {r2.status_code}')
if r2.status_code == 200:
    entries = json.loads(r2.data)
    print(f'  Entries: {len(entries)}')
    if entries:
        print(f'  First keys: {list(entries[0].keys())}')
        print(f'  First mood: {entries[0].get("mood", "?")}')

# Test chat still works
r3 = client.post('/chat/ask', json={'message': 'What are you thinking about?'})
print(f'POST /chat/ask -> {r3.status_code}')
if r3.status_code == 200:
    resp = json.loads(r3.data)
    print(f'  Response length: {len(resp.get("response", ""))}')

print('All checks done.')