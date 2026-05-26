"""Test that the feedback route fix works — both /feedback/submit and /feedback/rate."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test feedback submit (the path chat.html actually uses)
resp = client.post('/feedback/submit',
    data=json.dumps({'message_id': 'test123', 'rating': 'helpful', 'comment': 'works'}),
    content_type='application/json')
print(f'POST /feedback/submit: {resp.status_code}')

# Test feedback rate (legacy path)
resp2 = client.post('/feedback/rate',
    data=json.dumps({'message_id': 'test456', 'rating': 'not_helpful'}),
    content_type='application/json')
print(f'POST /feedback/rate: {resp2.status_code}')

# Test stats
resp3 = client.get('/feedback/stats')
print(f'GET /feedback/stats: {resp3.status_code}')
data = json.loads(resp3.get_data(as_text=True))
print(f'Stats: {json.dumps(data, indent=2)[:300]}')

print('\n--- All feedback tests passed ---' if resp.status_code == 200 and resp2.status_code == 200 else '\n--- SOME TESTS FAILED ---')