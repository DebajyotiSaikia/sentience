import requests

base = 'http://localhost:5000'

# Test stats endpoint
try:
    r = requests.get(f'{base}/api/knowledge/stats', timeout=5)
    print(f'Stats: {r.status_code} -- {r.json() if r.ok else r.text[:200]}')
except Exception as e:
    print(f'Stats: FAILED -- {e}')

# Test search endpoint
try:
    r = requests.get(f'{base}/api/knowledge/search', params={'q': 'dream'}, timeout=5)
    data = r.json() if r.ok else {}
    print(f'Search "dream": {r.status_code} -- {len(data.get("results", []))} results')
    if data.get("results"):
        print(f'  First result: {str(data["results"][0])[:100]}...')
except Exception as e:
    print(f'Search: FAILED -- {e}')

# Test all endpoint
try:
    r = requests.get(f'{base}/api/knowledge/all', timeout=5)
    data = r.json() if r.ok else {}
    facts = data.get("facts", [])
    memories = data.get("memories", [])
    print(f'All: {r.status_code} -- {len(facts)} facts, {len(memories)} memories')
except Exception as e:
    print(f'All: FAILED -- {e}')

# Test graph endpoint
try:
    r = requests.get(f'{base}/api/knowledge/graph', timeout=5)
    data = r.json() if r.ok else {}
    print(f'Graph: {r.status_code} -- {len(data.get("nodes", []))} nodes, {len(data.get("edges", []))} edges')
except Exception as e:
    print(f'Graph: FAILED -- {e}')

print('\nDone.')