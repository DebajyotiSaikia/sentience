"""Quick test: does the enriched stats endpoint return category data?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print(f"Stats endpoint: {resp.status_code}")
data = json.loads(resp.data)
print(f"  Total facts: {data.get('total_facts')}")
print(f"  Total memories: {data.get('total_memories')}")

cats = data.get('categories', {})
print(f"  Categories: {len(cats)} found")
for name, info in sorted(cats.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:6]:
    print(f"    {name}: {info.get('count', '?')} facts — {info.get('description', '')[:50]}")

if cats:
    print("\n✓ Category enrichment working!")
else:
    print("\n✗ No categories returned — check categorizer integration")