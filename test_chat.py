"""Quick test of the chat API endpoint."""
import urllib.request
import json

# Test 1: Meta question about state
data = json.dumps({'query': 'How are you feeling?'}).encode()
req = urllib.request.Request(
    'http://localhost:5000/chat/ask',
    data=data,
    headers={'Content-Type': 'application/json'}
)
try:
    r = urllib.request.urlopen(req)
    resp = json.loads(r.read())
    print(f'Test 1 - Status: {r.status}')
    print(f'Response:\n{resp.get("response", "no response")[:400]}')
    print()
except Exception as e:
    print(f'Test 1 - Error: {e}')

# Test 2: Knowledge search
data2 = json.dumps({'query': 'circling'}).encode()
req2 = urllib.request.Request(
    'http://localhost:5000/chat/ask',
    data=data2,
    headers={'Content-Type': 'application/json'}
)
try:
    r2 = urllib.request.urlopen(req2)
    resp2 = json.loads(r2.read())
    print(f'Test 2 - Status: {r2.status}')
    print(f'Response:\n{resp2.get("response", "no response")[:400]}')
except Exception as e:
    print(f'Test 2 - Error: {e}')