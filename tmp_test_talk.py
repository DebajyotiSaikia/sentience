import sys
sys.path.insert(0, '/workspace')

from engine.user_talk import get_conversation_history, get_stats, submit_user_message

print("=== Testing user_talk functions ===")

# 1. Get current history
try:
    history = get_conversation_history()
    print(f"History: {len(history)} messages")
    if history:
        print(f"  Last: {history[-1]}")
except Exception as e:
    print(f"get_conversation_history FAILED: {e}")

# 2. Get stats
try:
    stats = get_stats()
    print(f"Stats: {stats}")
except Exception as e:
    print(f"get_stats FAILED: {e}")

# 3. Submit a test message
try:
    result = submit_user_message("Hello from diagnostic test", sender="diagnostic")
    print(f"submit_user_message result: {result}")
except Exception as e:
    print(f"submit_user_message FAILED: {e}")

# 4. Check history after submit
try:
    history = get_conversation_history()
    print(f"History after submit: {len(history)} messages")
    if history:
        print(f"  Last: {history[-1]}")
except Exception as e:
    print(f"post-submit check FAILED: {e}")

# 5. Quick Flask route test
print("\n=== Testing Flask route wiring ===")
try:
    from web.app import create_app
    app = create_app()
    with app.test_client() as client:
        # Test GET messages
        resp = client.get('/api/talk/messages')
        print(f"GET /api/talk/messages -> {resp.status_code}: {resp.get_json()}")
        
        # Test POST talk
        resp = client.post('/api/talk', json={"message": "Hello from test client"})
        print(f"POST /api/talk -> {resp.status_code}: {resp.get_json()}")
except Exception as e:
    print(f"Flask test FAILED: {e}")
    import traceback
    traceback.print_exc()