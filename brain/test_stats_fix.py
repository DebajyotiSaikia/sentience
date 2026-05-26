"""Verify the knowledge stats endpoint returns correct fact count."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print('Status:', resp.status_code)
data = json.loads(resp.get_data(as_text=True))
print('Total facts:', data.get('total_facts'))
print('By source:', data.get('by_source', {}))

assert data['total_facts'] > 10, f'Still broken: only {data["total_facts"]} facts'
print('PASS — knowledge stats fixed')