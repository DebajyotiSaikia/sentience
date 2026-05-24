from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Does the knowledge hub page render?
print("=== Test 1: Knowledge Hub page ===")
resp = client.get('/knowledge-hub')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    html = resp.data.decode()
    print(f"  Length: {len(html)} chars")
    # Check key elements rendered
    has_facts = 'facts' in html
    has_search = 'Search' in html
    print(f"  Has 'facts' stat: {has_facts}")
    print(f"  Has search UI: {has_search}")
else:
    print(f"  Error: {resp.data.decode()[:300]}")

# Test 2: Does the search API work?
print("\n=== Test 2: Search API ===")
resp = client.get('/api/knowledge/search?q=identity')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    import json
    data = json.loads(resp.data)
    print(f"  Results: {len(data.get('results', []))}")
    for r in data.get('results', [])[:3]:
        print(f"    [{r.get('score',0):.2f}] {r.get('fact','')[:80]}")
else:
    print(f"  Error: {resp.data.decode()[:300]}")

# Test 3: Clusters API
print("\n=== Test 3: Clusters API ===")
resp = client.get('/api/knowledge/clusters')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    clusters = data.get('clusters', [])
    print(f"  Clusters: {len(clusters)}")
    for c in clusters[:3]:
        print(f"    {c.get('label','?')}: {len(c.get('facts',[]))} facts")
else:
    print(f"  Error: {resp.data.decode()[:300]}")

# Test 4: Questions API
print("\n=== Test 4: Questions API ===")
resp = client.get('/api/knowledge/questions')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    questions = data.get('questions', [])
    print(f"  Questions: {len(questions)}")
    for q in questions[:3]:
        print(f"    ? {q[:80]}")
else:
    print(f"  Error: {resp.data.decode()[:300]}")

print("\n=== Done ===")