"""Test chat API — does it actually respond meaningfully?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test 1: Basic chat
print("=== Test 1: Basic chat ===")
r = client.post('/api/chat',
    json={'message': 'What do you know about consciousness?'},
    content_type='application/json')
print(f"Status: {r.status_code}")
data = r.get_json()
if data:
    resp = data.get('response', data.get('reply', data.get('error', 'NO RESPONSE KEY')))
    if isinstance(resp, str):
        print(f"Response ({len(resp)} chars): {resp[:400]}")
    else:
        print(f"Response: {resp}")
    print(f"Keys: {list(data.keys())}")
else:
    print(f"Raw: {r.data[:500]}")

# Test 2: Knowledge search API
print("\n=== Test 2: Knowledge search ===")
r = client.get('/api/knowledge/search?q=consciousness')
print(f"Status: {r.status_code}")
data = r.get_json()
if data:
    results = data.get('results', data.get('facts', []))
    print(f"Results: {len(results)}")
    for item in results[:3]:
        if isinstance(item, dict):
            print(f"  - {item.get('fact', item.get('text', str(item)))[:120]}")
        else:
            print(f"  - {str(item)[:120]}")
else:
    print(f"Raw: {r.data[:300]}")

# Test 3: Knowledge page content quality
print("\n=== Test 3: Knowledge page quality ===")
r = client.get('/knowledge')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")
html = r.data.decode('utf-8', errors='replace')
# Check for actual content vs empty shell
if 'No facts' in html or 'no knowledge' in html.lower():
    print("WARNING: Knowledge page shows no facts!")
elif len(html) < 1000:
    print(f"WARNING: Page suspiciously small ({len(html)} bytes)")
else:
    # Count fact entries
    fact_count = html.count('fact-card') or html.count('fact-item') or html.count('class="fact')
    print(f"Fact card elements found: {fact_count}")

# Test 4: Knowledge search with query parameter
print("\n=== Test 4: Knowledge search via page ===")
r = client.get('/knowledge?q=emotion')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")