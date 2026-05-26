"""Test knowledge API endpoints after the path fix."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

print("=" * 50)
print("KNOWLEDGE API ENDPOINT TESTS")
print("=" * 50)

# Test 1: Stats endpoint
resp = client.get('/api/knowledge/stats')
print(f"\n[1] GET /api/knowledge/stats -> {resp.status_code}")
print(f"    Body: {resp.get_data(as_text=True)[:200]}")

# Test 2: Search endpoint
resp2 = client.get('/api/knowledge/search?q=identity')
print(f"\n[2] GET /api/knowledge/search?q=identity -> {resp2.status_code}")
print(f"    Body: {resp2.get_data(as_text=True)[:300]}")

# Test 3: Search with no query
resp3 = client.get('/api/knowledge/search')
print(f"\n[3] GET /api/knowledge/search (no query) -> {resp3.status_code}")
print(f"    Body: {resp3.get_data(as_text=True)[:200]}")

# Test 4: Knowledge explorer page
resp4 = client.get('/knowledge')
print(f"\n[4] GET /knowledge -> {resp4.status_code}")
has_content = len(resp4.get_data(as_text=True)) > 500
print(f"    Has substantial content: {has_content}")

# Test 5: Explore page
resp5 = client.get('/explore')
print(f"\n[5] GET /explore -> {resp5.status_code}")

# Test 6: Chat page
resp6 = client.get('/chat')
print(f"\n[6] GET /chat -> {resp6.status_code}")

print("\n" + "=" * 50)
all_ok = all(r.status_code == 200 for r in [resp, resp2, resp3, resp4, resp5, resp6])
print(f"ALL PASSED: {all_ok}")