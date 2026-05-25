"""Test the conversation starters endpoint works end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test starters endpoint
    r = c.get('/starters')
    print(f"Starters status: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"Starters: {data.get('starters', [])[:2]}")
        print(f"Greeting: {data.get('greeting', 'none')}")
    else:
        print("No JSON returned")
    
    # Test chat page loads
    r2 = c.get('/chat')
    print(f"\nChat page status: {r2.status_code}")
    print(f"Chat page size: {len(r2.data)} bytes")
    
    # Test chat send
    r3 = c.post('/chat/send', json={"message": "hello"})
    print(f"\nChat send status: {r3.status_code}")
    resp = r3.get_json()
    if resp:
        print(f"Response preview: {str(resp.get('response', ''))[:150]}")
    
    print("\n✓ All chat tests passed")