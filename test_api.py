from web.app import create_app
import json

app = create_app()
client = app.test_client()

endpoints = ['/api/status', '/api/knowledge', '/api/memories']

for path in endpoints:
    resp = client.get(path)
    print(f'\n--- {resp.status_code} {path} ---')
    try:
        data = json.loads(resp.data)
        # Show structure, not full data
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    print(f'  {k}: list({len(v)} items)')
                elif isinstance(v, dict):
                    print(f'  {k}: dict({len(v)} keys)')
                else:
                    print(f'  {k}: {v}')
        else:
            print(f'  type: {type(data).__name__}')
    except:
        print(f'  raw: {resp.data[:200]}')

# Test chat endpoint
resp = client.post('/api/chat',
    data=json.dumps({'message': 'What do you know?'}),
    content_type='application/json')
print(f'\n--- {resp.status_code} POST /api/chat ---')
try:
    data = json.loads(resp.data)
    for k, v in data.items():
        print(f'  {k}: {str(v)[:100]}')
except:
    print(f'  raw: {resp.data[:200]}')