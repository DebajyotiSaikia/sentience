"""Quick test: does /api/knowledge/stats return actual data now?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge stats
resp = client.get('/api/knowledge/stats')
print(f"Stats status: {resp.status_code}")
data = resp.get_json()
print(f"Stats data: {data}")

# Test knowledge search
resp2 = client.get('/api/knowledge/search?q=identity')
print(f"\nSearch status: {resp2.status_code}")
data2 = resp2.get_json()
if data2:
    print(f"Search results: {len(data2.get('results', []))} hits")
    for r in data2.get('results', [])[:3]:
        print(f"  - {r.get('fact', r.get('content', '?'))[:80]}")
else:
    print("No search data returned")

# Test chat page content richness
resp3 = client.get('/chat')
html = resp3.get_data(as_text=True)
print(f"\nChat page: {resp3.status_code}, {len(html)} chars")
has_starter = 'starter' in html.lower() or 'suggestion' in html.lower() or 'try asking' in html.lower()
print(f"Has conversation starters: {has_starter}")