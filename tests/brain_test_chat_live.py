"""Quick test: is the chat endpoint actually working?"""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test GET /chat
r1 = client.get('/chat')
print(f'GET /chat: {r1.status_code}')

# Test POST /chat/ask (the actual endpoint)
r2 = client.post('/chat/ask', json={'message': 'hello'}, content_type='application/json')
print(f'POST /chat/ask: {r2.status_code}')
print(f'Response: {r2.get_data(as_text=True)[:500]}')

# Test POST /api/chat (alternate endpoint)
r3 = client.post('/api/chat', json={'message': 'hello'}, content_type='application/json')
print(f'POST /api/chat: {r3.status_code}')
print(f'Response: {r3.get_data(as_text=True)[:500]}')

# List chat routes
print('\nChat routes:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'chat' in rule.rule:
        methods = ','.join(rule.methods - {'OPTIONS', 'HEAD'})
        print(f'  {rule.rule} [{methods}]')