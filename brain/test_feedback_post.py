"""Minimal test: does POST /api/feedback work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# List all registered routes first
print("=== REGISTERED ROUTES containing 'feedback' ===")
for rule in app.url_map.iter_rules():
    if 'feedback' in str(rule):
        print(f"  {rule.methods} {rule}")

print("\n=== TEST: POST /api/feedback ===")
resp = client.post('/api/feedback',
    data=json.dumps({
        'response_id': 'test-123',
        'rating': 4,
        'comment': 'test feedback'
    }),
    content_type='application/json')
print(f"Status: {resp.status_code}")
print(f"Body: {resp.get_data(as_text=True)[:300]}")

print("\n=== TEST: POST /feedback/submit ===")
resp2 = client.post('/feedback/submit',
    data=json.dumps({
        'response_id': 'test-123',
        'rating': 4,
        'comment': 'test feedback'
    }),
    content_type='application/json')
print(f"Status: {resp2.status_code}")
print(f"Body: {resp2.get_data(as_text=True)[:300]}")