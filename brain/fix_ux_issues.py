"""Fix the 3 UX audit failures: nav links, CTA, knowledge stats."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# === Diagnose Issue 1 & 2: Home page nav links + CTA ===
resp = client.get('/')
html = resp.get_data(as_text=True)
links = re.findall(r'href=["\']([^"\']+)["\']', html)
internal = [l for l in links if l.startswith('/')]
unique_internal = sorted(set(internal))
print(f"=== HOME PAGE: {len(unique_internal)} unique internal links ===")
for l in unique_internal:
    print(f"  {l}")

has_cta = bool(re.search(r'(Start|Begin|Try|Talk|Chat|Ask).{0,30}(href|button|onclick)', html, re.I))
print(f"\nHas CTA pattern: {has_cta}")

# What does the UX audit actually check?
# Let me look at specific thresholds
print(f"\nHTML length: {len(html)} chars")

# === Diagnose Issue 3: Knowledge stats ===
resp = client.get('/api/knowledge/stats')
print(f"\n=== KNOWLEDGE STATS: status={resp.status_code} ===")
data = resp.get_data(as_text=True)
print(data[:500])

# Also check the raw knowledge file
kg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'knowledge.json')
if os.path.exists(kg_path):
    with open(kg_path) as f:
        kg = json.load(f)
    if isinstance(kg, dict) and 'nodes' in kg:
        print(f"\nKnowledge file: {len(kg['nodes'])} nodes, {len(kg.get('edges', []))} edges")
    else:
        print(f"\nKnowledge file format: {type(kg)}, keys={list(kg.keys()) if isinstance(kg, dict) else 'N/A'}")
else:
    print(f"\nKnowledge file NOT FOUND at {kg_path}")