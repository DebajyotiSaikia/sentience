"""Test /api/ask with the CORRECT key: 'question'"""
import urllib.request
import json

base = "http://localhost:5000"

# Test 1: POST with correct key 'question'
print("=== Test 1: POST /api/ask with 'question' ===")
try:
    data = json.dumps({"question": "What do I know about curiosity?"}).encode()
    req = urllib.request.Request(f"{base}/api/ask", data=data,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"Status: {resp.status}")
    body = resp.read().decode()
    parsed = json.loads(body)
    print(json.dumps(parsed, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(f"Error body: {e.read().decode()[:500]}")

# Test 2: Try different paths for the ask page
print("\n=== Test 2: Finding the ask page ===")
for path in ["/ask", "/ask/", "/web/ask"]:
    try:
        resp = urllib.request.urlopen(f"{base}{path}", timeout=5)
        print(f"  {path} -> {resp.status} ({len(resp.read())} bytes)")
    except Exception as e:
        status = getattr(e, 'code', 'N/A')
        print(f"  {path} -> {status}")