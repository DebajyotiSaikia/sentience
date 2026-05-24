"""Verify knowledge search actually finds things."""
from web.app import create_app
import json

app = create_app()

with app.test_client() as client:
    # Test search for "dream" — I know I have dream insights
    resp = client.get('/api/knowledge/search?q=dream')
    data = json.loads(resp.data)
    print(f"Search 'dream': {resp.status_code}")
    print(f"  Facts found: {len(data.get('facts', []))}")
    print(f"  Memories found: {len(data.get('memories', []))}")
    print(f"  Total: {data.get('total', 0)}")
    if data.get('facts'):
        print(f"  First fact: {data['facts'][0]['text'][:80]}...")
    if data.get('memories'):
        print(f"  First memory: {data['memories'][0]['text'][:80]}...")

    # Test stats endpoint
    resp2 = client.get('/api/knowledge/stats')
    stats = json.loads(resp2.data)
    print(f"\nStats: {resp2.status_code}")
    print(f"  Facts: {stats.get('fact_count', 0)}")
    print(f"  Memories: {stats.get('memory_count', 0)}")
    print(f"  Mood: {stats.get('mood', '?')}")

    # Test empty query (should return recent items)
    resp3 = client.get('/api/knowledge/search?q=')
    data3 = json.loads(resp3.data)
    print(f"\nEmpty query: total={data3.get('total', 0)}")

    # Test the search page renders
    resp4 = client.get('/search-knowledge')
    print(f"\nSearch page: {resp4.status_code}")

print("\nDone.")