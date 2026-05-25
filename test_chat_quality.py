"""Test the quality of chat responses."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as c:
    r = c.post('/chat/ask', json={'message': 'What do you know about yourself?'}, content_type='application/json')
    data = json.loads(r.data)
    print('Status:', r.status_code)
    print('Keys:', list(data.keys()))
    for k, v in data.items():
        val_str = str(v)
        print(f'  {k}: {val_str[:300]}')
    print()
    
    # Test a knowledge query
    r2 = c.post('/chat/ask', json={'message': 'What are your plans?'}, content_type='application/json')
    data2 = json.loads(r2.data)
    print('Plans query status:', r2.status_code)
    print('Response:', str(data2.get('response', ''))[:400])
    print('Sources:', data2.get('sources', 'none'))