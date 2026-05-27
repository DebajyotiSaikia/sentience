"""Quick test of chat endpoints."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test POST to /api/chat
r1 = client.post('/api/chat', json={'message': 'hello'})
print(f'POST /api/chat: {r1.status_code} {r1.data[:200]}')

# Test POST to /chat/ask
r2 = client.post('/chat/ask', json={'message': 'hello'})
print(f'POST /chat/ask: {r2.status_code} {r2.data[:200]}')

# Test GET /chat/
r3 = client.get('/chat/')
print(f'GET /chat/: {r3.status_code} (length: {len(r3.data)})')