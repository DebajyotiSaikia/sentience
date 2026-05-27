"""Diagnose the three UX audit failures."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
c = app.test_client()

# 1. Check knowledge stats
print("=== KNOWLEDGE STATS ===")
r = c.get('/api/knowledge/stats')
print(f"Status: {r.status_code}")
print(f"Response: {r.get_data(as_text=True)[:500]}")

# 2. Check home page for navigation
print("\n=== HOME PAGE NAV CHECK ===")
r = c.get('/')
html = r.get_data(as_text=True)
has_chat_link = '/chat' in html
has_explore_link = '/explore' in html
has_nav = 'nav' in html.lower()
has_links = html.count('href=') 
print(f"Has /chat link: {has_chat_link}")
print(f"Has /explore link: {has_explore_link}")
print(f"Has nav element: {has_nav}")
print(f"Total href count: {has_links}")

# Check if index.html template exists and is used
print("\n=== INDEX TEMPLATE CHECK ===")
if os.path.exists('web/templates/index.html'):
    with open('web/templates/index.html') as f:
        idx = f.read()
    print(f"index.html exists, {len(idx)} chars")
    print(f"Has href to /chat: {'/chat' in idx}")
    print(f"Has href to /explore: {'/explore' in idx}")
    print(f"Has nav-bar class: {'nav-bar' in idx}")
    print(f"Has nav.js: {'nav.js' in idx}")
else:
    print("index.html NOT FOUND")

# 3. Check knowledge.json structure
print("\n=== KNOWLEDGE DATA ===")
kpath = 'brain/knowledge.json'
if os.path.exists(kpath):
    with open(kpath) as f:
        data = json.load(f)
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        if 'nodes' in data:
            nodes = data['nodes']
            print(f"Node count: {len(nodes)}")
            # Show first node
            if nodes:
                first_key = list(nodes.keys())[0] if isinstance(nodes, dict) else 0
                print(f"First node key: {first_key}")
                print(f"First node: {str(nodes[first_key])[:200]}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
else:
    print("knowledge.json NOT FOUND")

# 4. What does the stats endpoint actually return?
print("\n=== STATS ENDPOINT DETAIL ===")
stats_data = json.loads(r.get_data(as_text=True)) if r.status_code == 200 else {}
print(json.dumps(stats_data, indent=2)[:600])