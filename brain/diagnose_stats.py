"""Diagnose the /api/knowledge/stats discrepancy."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. What's actually in brain/knowledge.json?
with open('brain/knowledge.json') as f:
    data = json.load(f)
print(f"brain/knowledge.json type: {type(data).__name__}")
if isinstance(data, dict):
    print(f"  Keys: {list(data.keys())[:5]}")
    if 'nodes' in data:
        print(f"  nodes count: {len(data['nodes'])}")
    print(f"  Top-level keys count: {len(data)}")

# 2. What does the stats endpoint actually return?
from web.app import create_app
app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print(f"\n/api/knowledge/stats -> {resp.status_code}")
stats = json.loads(resp.data)
print(f"  Response: {json.dumps(stats, indent=2)[:500]}")

# 3. Check which blueprint is serving it
print(f"\nAll registered rules containing 'stats':")
for rule in app.url_map.iter_rules():
    if 'stats' in str(rule):
        print(f"  {rule} -> {rule.endpoint}")

# 4. What does the knowledge_live _load_knowledge return?
try:
    from web.knowledge_live import _load_knowledge
    facts = _load_knowledge()
    print(f"\nknowledge_live._load_knowledge() returns {len(facts)} items")
except Exception as e:
    print(f"\nknowledge_live._load_knowledge() error: {e}")