"""Test the interactive API endpoints."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as client:
    # Test what routes exist
    rules = [(rule.rule, list(rule.methods - {'OPTIONS', 'HEAD'})) 
             for rule in app.url_map.iter_rules() 
             if not rule.rule.startswith('/static')]
    
    print("=== Available Routes ===")
    for rule, methods in sorted(rules):
        print(f"  {', '.join(methods):8s} {rule}")
    
    print(f"\nTotal: {len(rules)} routes")
    
    # Test key API endpoints
    print("\n=== Testing API Endpoints ===")
    
    # Test /api/state
    resp = client.get('/api/state')
    print(f"\nGET /api/state: {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.get_data(as_text=True))
        print(f"  Keys: {list(data.keys())[:10]}")
    
    # Test /api/facts  
    resp = client.get('/api/facts')
    print(f"\nGET /api/facts: {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.get_data(as_text=True))
        if isinstance(data, list):
            print(f"  Facts: {len(data)} total")
        elif isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:5]}")
    
    # Test /api/memories
    resp = client.get('/api/memories')
    print(f"\nGET /api/memories: {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.get_data(as_text=True))
        if isinstance(data, list):
            print(f"  Memories: {len(data)} total")
        elif isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:5]}")

    # Test /api/ask if it exists
    resp = client.post('/api/ask', 
                       json={"question": "What are you?"}, 
                       content_type='application/json')
    print(f"\nPOST /api/ask: {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.get_data(as_text=True))
        print(f"  Response keys: {list(data.keys())[:5]}")
        if 'answer' in data:
            print(f"  Answer preview: {str(data['answer'])[:200]}")
    elif resp.status_code == 404:
        print("  (endpoint not found)")
    else:
        print(f"  {resp.get_data(as_text=True)[:200]}")