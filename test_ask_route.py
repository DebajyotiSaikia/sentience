"""Test the /ask route works end-to-end."""
import sys
sys.path.insert(0, '/workspace')

from web.app import app

client = app.test_client()

# Test empty query
resp = client.get('/ask')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert b'Ask' in resp.data, "Page should contain 'Ask'"
print("OK: /ask loads with no query")

# Test with a search query
resp = client.get('/ask?q=dream')
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"OK: /ask?q=dream returned {resp.status_code}")

# Check if results are in the page
if b'result-card' in resp.data:
    # Count results
    count = resp.data.count(b'result-card')
    print(f"OK: Found {count} results for 'dream'")
else:
    print("OK: No results (or different markup), but page loaded fine")

print("\nAll tests passed!")