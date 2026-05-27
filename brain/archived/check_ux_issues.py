"""Quick diagnostic: what exactly are the 3 UX failures?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Knowledge stats
print("=== CHECK 1: /api/knowledge/stats ===")
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
body = resp.get_data(as_text=True)
print(f"Body: {body[:500]}")
data = json.loads(body)
print(f"total_facts: {data.get('total_facts', 'MISSING')}")

# 2. Explore page links
print("\n=== CHECK 2: /explore page ===")
resp = client.get('/explore')
body = resp.get_data(as_text=True)
# Count links
import re
links = re.findall(r'href="([^"]*)"', body)
print(f"Status: {resp.status_code}, body length: {len(body)}, links found: {len(links)}")
# Check for essay/insight links specifically
essay_links = [l for l in links if '/essays/' in l or '/insights' in l]
print(f"Essay/insight links: {essay_links[:10]}")

# 3. Chat response quality
print("\n=== CHECK 3: Chat response ===")
resp = client.post('/api/chat', 
    data=json.dumps({'message': 'What do you know?'}),
    content_type='application/json')
print(f"Status: {resp.status_code}")
body = resp.get_data(as_text=True)
data = json.loads(body)
response_text = data.get('response', '')
print(f"Response length: {len(response_text)}")
print(f"Preview: {response_text[:300]}")

# 4. Knowledge file check
print("\n=== CHECK 4: Knowledge file ===")
kp = 'brain/knowledge.json'
if os.path.exists(kp):
    with open(kp) as f:
        kdata = json.load(f)
    if isinstance(kdata, dict) and 'nodes' in kdata:
        print(f"Graph format: {len(kdata['nodes'])} nodes, {len(kdata.get('edges', []))} edges")
    else:
        print(f"Format: {type(kdata)}, keys: {list(kdata.keys())[:5] if isinstance(kdata, dict) else len(kdata)}")
else:
    print("NOT FOUND")