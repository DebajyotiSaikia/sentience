"""Test the knowledge search API endpoints."""
import sys
sys.path.insert(0, '/home/xt/agent')

from web.search import knowledge_bp
from flask import Flask

app = Flask(__name__)
app.register_blueprint(knowledge_bp)

# List all routes
print("=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        print(f"  {rule.methods - {'HEAD', 'OPTIONS'}} {rule.rule} -> {rule.endpoint}")

# Test the search function directly
from web.search import search_knowledge
results = search_knowledge("dream")
print(f"\n=== Search 'dream' -> {len(results)} results ===")
for r in results[:3]:
    print(f"  [{r.get('score', '?'):.2f}] {r.get('text', r.get('fact', ''))[:80]}")

# Test stats
from web.search import get_knowledge_stats
stats = get_knowledge_stats()
print(f"\n=== Knowledge Stats ===")
for k, v in stats.items():
    print(f"  {k}: {v}")

print("\nAll tests passed!")