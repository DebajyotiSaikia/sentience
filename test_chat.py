"""Test the chat blueprint is properly wired and functional."""
import sys
sys.path.insert(0, '/workspace')

# Test 1: Can we import the chat blueprint?
try:
    from web.chat import chat_bp
    print("✓ chat_bp imported successfully")
    print(f"  Name: {chat_bp.name}")
except Exception as e:
    print(f"✗ Failed to import chat_bp: {e}")
    sys.exit(1)

# Test 2: Can we create the app and see chat routes?
try:
    from web.app import create_app
    app = create_app()
    chat_routes = [r for r in app.url_map.iter_rules() if 'chat' in r.rule]
    print(f"\n✓ App created, found {len(chat_routes)} chat routes:")
    for r in chat_routes:
        print(f"  {r.methods - {'HEAD', 'OPTIONS'}} {r.rule}")
except Exception as e:
    print(f"✗ Failed to create app: {e}")
    sys.exit(1)

# Test 3: Can we hit the chat page?
try:
    with app.test_client() as client:
        resp = client.get('/chat/')
        print(f"\n✓ GET /chat/ -> {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_data(as_text=True)
            print(f"  Response length: {len(data)} chars")
except Exception as e:
    print(f"✗ Failed to test chat page: {e}")

# Test 4: Can we POST to chat?
try:
    with app.test_client() as client:
        resp = client.post('/chat/send', json={'message': 'Hello, who are you?'})
        print(f"\n✓ POST /chat/send -> {resp.status_code}")
        data = resp.get_json() if resp.status_code == 200 else resp.get_data(as_text=True)
        print(f"  Response: {str(data)[:300]}")
except Exception as e:
    print(f"✗ Failed to POST to chat: {e}")

print("\n=== Done ===")