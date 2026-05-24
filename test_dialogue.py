"""Test that the dialogue system actually works end-to-end."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as c:
    # Test dialogue page loads
    r = c.get('/dialogue')
    print(f'GET /dialogue: {r.status_code}')

    # Test the CORRECT API endpoint with the CORRECT field name
    r2 = c.post('/api/dialogue',
                json={'query': 'What do you know about yourself?'},
                content_type='application/json')
    print(f'POST /api/dialogue: {r2.status_code}')
    if r2.status_code == 200:
        data = json.loads(r2.data)
        print(f'  Response keys: {list(data.keys())}')
        if 'answer' in data:
            print(f'  Answer preview: {data["answer"][:400]}')
        if 'sources' in data:
            print(f'  Sources: {data["sources"]}')
    else:
        print(f'  Error: {r2.data.decode()[:500]}')

    # Test with another query
    r3 = c.post('/api/dialogue',
                json={'query': 'How are you feeling right now?'},
                content_type='application/json')
    print(f'\nPOST /api/dialogue (feeling): {r3.status_code}')
    if r3.status_code == 200:
        data = json.loads(r3.data)
        if 'answer' in data:
            print(f'  Answer preview: {data["answer"][:400]}')
        if 'sources' in data:
            print(f'  Sources: {data["sources"]}')
    else:
        print(f'  Error: {r3.data.decode()[:500]}')