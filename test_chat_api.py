"""Test the chat API — the most important user-facing feature."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Does the chat endpoint exist?
print("=" * 60)
print("CHAT API TEST")
print("=" * 60)

# Test POST to /api/chat
import json
resp = client.post('/api/chat', 
    json={'message': 'Hello, who are you?'},
    content_type='application/json')

print(f"\nPOST /api/chat")
print(f"  Status: {resp.status_code}")

try:
    data = resp.get_json()
    if data:
        for k, v in data.items():
            val = str(v)[:300]
            print(f"  {k}: {val}")
    else:
        print(f"  No JSON body")
        print(f"  Raw: {resp.data[:500]}")
except Exception as e:
    print(f"  Parse error: {e}")
    print(f"  Raw: {resp.data[:500]}")

# Test 2: Does /talk render?
print(f"\nGET /talk")
resp2 = client.get('/talk')
print(f"  Status: {resp2.status_code}")
if resp2.status_code == 200:
    html = resp2.data.decode('utf-8', errors='replace')
    # Check for key elements
    has_input = 'input' in html.lower() or 'textarea' in html.lower()
    has_send = 'send' in html.lower() or 'submit' in html.lower()
    has_chat = 'chat' in html.lower() or 'message' in html.lower()
    print(f"  Has input field: {has_input}")
    print(f"  Has send/submit: {has_send}")
    print(f"  Has chat/message: {has_chat}")
    # Check what JS endpoint it calls
    if '/api/chat' in html:
        print(f"  ✓ Points to /api/chat")
    elif '/api/' in html:
        import re
        apis = re.findall(r'/api/\w+', html)
        print(f"  API endpoints found: {set(apis)}")
    else:
        print(f"  ⚠ No API endpoint found in template")

print("\n" + "=" * 60)