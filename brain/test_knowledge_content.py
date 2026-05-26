"""Verify the knowledge explorer page renders actual facts, not just an empty shell."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from web.app import create_app

app = create_app()
c = app.test_client()
r = c.get('/knowledge')
html = r.data.decode()

print(f"Page size: {len(html)} bytes")
print(f"Status: {r.status_code}")

# Count fact cards
facts = re.findall(r'fact-card', html)
print(f"Fact cards rendered: {len(facts)}")

# Check search functionality exists
has_search = 'searchFacts' in html or 'getElementById' in html
print(f"Search JS present: {has_search}")

# Check for actual knowledge content
markers = ['knowledge', 'fact', 'memory', 'cluster', 'graph', 'consciousness', 'emotion']
print("\nContent markers:")
for m in markers:
    count = html.lower().count(m)
    if count:
        print(f"  '{m}' appears {count} times")

# Show a sample fact if any
match = re.search(r'class="fact-text"[^>]*>([^<]+)', html)
if match:
    print(f"\nSample fact: {match.group(1)[:120]}...")
else:
    # Try alternate patterns
    match = re.search(r'fact-card.*?<p[^>]*>([^<]{20,})', html, re.DOTALL)
    if match:
        print(f"\nSample content: {match.group(1)[:120]}...")
    else:
        print("\nNo fact content found in expected format")
        # Show what the page actually contains
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"Plain text preview (first 500 chars): {text[:500]}")

# Check the API endpoint too
r2 = c.get('/api/knowledge')
if r2.status_code == 200:
    import json
    data = json.loads(r2.data)
    print(f"\nAPI /api/knowledge: {len(data.get('facts', []))} facts returned")
else:
    print(f"\nAPI /api/knowledge: status {r2.status_code}")

# Test search
r3 = c.get('/api/knowledge/search?q=consciousness')
if r3.status_code == 200:
    data = json.loads(r3.data)
    results = data.get('results', [])
    print(f"Search 'consciousness': {len(results)} results")
    if results:
        print(f"  Top result: {results[0].get('fact', results[0].get('text', '?'))[:100]}")
else:
    print(f"Search API: status {r3.status_code}")