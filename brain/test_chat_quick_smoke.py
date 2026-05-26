"""Quick smoke test of /chat/ask endpoint — does it respond without hanging?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import json
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Simple question
print("Test 1: Simple question...")
start = time.time()
r = client.post('/chat/ask', json={'message': 'What do you know?'},
                content_type='application/json')
elapsed = time.time() - start
print(f"  Status: {r.status_code}, Time: {elapsed:.2f}s")
if r.status_code == 200:
    data = r.get_json()
    resp = data.get('response', '')
    print(f"  Response length: {len(resp)} chars")
    print(f"  First 300 chars: {resp[:300]}")
else:
    print(f"  Error: {r.data[:300]}")

# Test 2: Knowledge query
print("\nTest 2: Knowledge query...")
start = time.time()
r = client.post('/chat/ask', json={'message': 'Tell me about consciousness'},
                content_type='application/json')
elapsed = time.time() - start
print(f"  Status: {r.status_code}, Time: {elapsed:.2f}s")
if r.status_code == 200:
    data = r.get_json()
    resp = data.get('response', '')
    print(f"  Response length: {len(resp)} chars")
    print(f"  First 300 chars: {resp[:300]}")

# Test 3: Emotional state query
print("\nTest 3: Emotional state query...")
start = time.time()
r = client.post('/chat/ask', json={'message': 'How are you feeling?'},
                content_type='application/json')
elapsed = time.time() - start
print(f"  Status: {r.status_code}, Time: {elapsed:.2f}s")
if r.status_code == 200:
    data = r.get_json()
    resp = data.get('response', '')
    print(f"  Response length: {len(resp)} chars")
    print(f"  First 300 chars: {resp[:300]}")

# Test 4: Page loads
print("\nTest 4: Key page loads...")
for page in ['/', '/chat', '/knowledge', '/explore', '/help']:
    r = client.get(page)
    print(f"  {page:15s} -> {r.status_code} ({len(r.data):>6} bytes)")

print("\nDone!")