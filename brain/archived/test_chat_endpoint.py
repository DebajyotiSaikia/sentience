"""Test the /chat/ask endpoint integration using Flask test client."""
import sys
sys.path.insert(0, '/workspace')

def test_endpoint():
    """Test the ask endpoint directly via Flask test client."""
    import json
    
    # Import the Flask app 
    try:
        from web.app import create_app
    except ImportError:
        # Try alternate app creation
        from flask import Flask
        from web.chat import chat_bp
        app = Flask(__name__)
        app.register_blueprint(chat_bp)
        client = app.test_client()
        return run_tests(client)
    
    app = create_app()
    client = app.test_client()
    return run_tests(client)

def run_tests(client):
    import json
    
    test_cases = [
        ("What are you feeling right now?", "feeling"),
        ("What are you working on?", "plan"),
        ("Hello!", "greeting"),
        ("Tell me something interesting", "knowledge"),
    ]
    
    passed = 0
    failed = 0
    
    for query, label in test_cases:
        resp = client.post('/chat/ask',
                          data=json.dumps({'query': query}),
                          content_type='application/json')
        
        if resp.status_code != 200:
            print(f"FAIL [{label}] HTTP {resp.status_code}: {query}")
            print(f"  Body: {resp.data[:200]}")
            failed += 1
            continue
        
        data = resp.get_json()
        
        # Check required fields
        has_response = 'response' in data and len(data['response']) > 10
        has_query = 'query' in data and data['query'] == query
        has_id = 'response_id' in data
        
        if has_response and has_query and has_id:
            preview = data['response'][:120]
            print(f"PASS [{label}] {query}")
            print(f"  → {preview}...")
            passed += 1
        else:
            print(f"FAIL [{label}] Missing fields: response={has_response}, query={has_query}, id={has_id}")
            failed += 1
    
    # Test error cases
    resp = client.post('/chat/ask', data='{}', content_type='application/json')
    if resp.status_code == 400:
        print(f"PASS [error] Empty query returns 400")
        passed += 1
    else:
        print(f"FAIL [error] Expected 400, got {resp.status_code}")
        failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    return failed == 0

if __name__ == '__main__':
    success = test_endpoint()
    sys.exit(0 if success else 1)