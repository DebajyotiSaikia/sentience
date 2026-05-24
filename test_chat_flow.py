"""Test whether the chat interface is actually wired up and working."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as c:
    # Test the chat page loads
    r = c.get('/chat/')
    print(f'GET /chat/ status: {r.status_code}')
    
    # Test /chat/ask endpoint
    r2 = c.post('/chat/ask', 
                data=json.dumps({'message': 'what do you know?'}),
                content_type='application/json')
    print(f'POST /chat/ask status: {r2.status_code}')
    if r2.status_code == 200:
        data = json.loads(r2.data)
        print(f'Response keys: {list(data.keys())}')
        resp_text = data.get("response", data.get("answer", ""))
        print(f'Response preview: {str(resp_text)[:400]}')
    else:
        print(f'Error: {r2.data[:500]}')
    
    # Test /api/chat endpoint
    r3 = c.post('/api/chat',
                data=json.dumps({'message': 'how are you feeling?'}),
                content_type='application/json')
    print(f'POST /api/chat status: {r3.status_code}')
    if r3.status_code == 200:
        data = json.loads(r3.data)
        print(f'Response keys: {list(data.keys())}')
        resp_text = data.get("response", data.get("answer", ""))
        print(f'Response preview: {str(resp_text)[:400]}')
    else:
        print(f'Error: {r3.data[:500]}')

    # Test /chat/status
    r4 = c.get('/chat/status')
    print(f'GET /chat/status: {r4.status_code}')
    if r4.status_code == 200:
        data = json.loads(r4.data)
        print(f'Status keys: {list(data.keys())}')

print('\nDone.')