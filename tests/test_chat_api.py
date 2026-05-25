from web.app import create_app
import json

app = create_app()
client = app.test_client()

resp = client.post('/api/chat', 
    data=json.dumps({'message': 'What do you know about yourself?'}), 
    content_type='application/json')

print('Status:', resp.status_code)
print('Response:', resp.get_data(as_text=True)[:500])