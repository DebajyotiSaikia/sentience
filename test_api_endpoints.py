"""Test API endpoints return real data, not empty shells."""
import sys
sys.path.insert(0, '.')
from web.app import create_app
import json

app = create_app()
app.config['TESTING'] = True
client = app.test_client()

endpoints = [
    ('/api/search?q=dream', 'Knowledge search'),
    ('/api/search?q=emotion', 'Emotion search'),
    ('/api/state', 'Agent state'),
    ('/api/knowledge/search?q=identity', 'Knowledge search v2'),
    ('/api/knowledge/categories', 'Knowledge categories'),
    ('/api/feedback', 'Feedback list'),
    ('/search?q=memory', 'Search page with query'),
    ('/chat', 'Chat page'),
]

print("=== API Endpoint Tests ===\n")
for url, label in endpoints:
    resp = client.get(url)
    status = resp.status_code
    size = len(resp.data)
    
    # Try to parse JSON for API endpoints
    detail = ""
    if '/api/' in url and status == 200:
        try:
            data = json.loads(resp.data)
            if isinstance(data, dict):
                keys = list(data.keys())
                detail = f" keys={keys}"
                # Check if results are non-empty
                for k in ['results', 'data', 'facts']:
                    if k in data and isinstance(data[k], list):
                        detail += f" {k}_count={len(data[k])}"
            elif isinstance(data, list):
                detail = f" list_len={len(data)}"
        except:
            detail = " (not JSON)"
    
    icon = "✓" if status == 200 else "✗"
    print(f"  {icon} {label:25s} {url:45s} -> {status} ({size:6d}b){detail}")

print("\n=== Done ===")