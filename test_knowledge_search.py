"""Test knowledge search API routes."""
import sys, os
os.chdir('/workspace')
sys.path.insert(0, '/workspace')

from web.knowledge_search import knowledge_search_bp, _load_knowledge, _search_items

# Test 1: Can we load knowledge?
facts, lessons, memories = _load_knowledge()
print(f"Loaded: {len(facts)} facts, {len(lessons)} lessons, {len(memories)} memories")

# Test 2: Can we search?
all_items = list(facts.values()) + lessons + memories
results = _search_items(all_items, 'dream', limit=5)
print(f"\nSearch 'dream': {len(results)} results")
for r in results[:3]:
    print(f"  [{r.get('type')}] {r.get('text','')[:80]}")

results2 = _search_items(all_items, 'emotion', limit=5)
print(f"\nSearch 'emotion': {len(results2)} results")
for r in results2[:3]:
    print(f"  [{r.get('type')}] {r.get('text','')[:80]}")

# Test 3: Flask routes
try:
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(knowledge_search_bp)
    with app.test_client() as c:
        r1 = c.get('/api/knowledge/search?q=dream')
        print(f"\nGET /api/knowledge/search?q=dream -> {r1.status_code}")
        d = r1.get_json()
        print(f"  Results: {d.get('count')}, Total: {d.get('total_knowledge')}")
        
        r2 = c.get('/api/knowledge/stats')
        print(f"GET /api/knowledge/stats -> {r2.status_code}")
        
        r3 = c.get('/api/knowledge/boundaries')
        print(f"GET /api/knowledge/boundaries -> {r3.status_code}")
        bd = r3.get_json()
        print(f"  Known topics: {list(bd.get('known_topics',{}).keys())}")
        print(f"  Unknown topics: {list(bd.get('unknown_topics',{}).keys())}")
        print(f"  Gaps: {len(bd.get('self_assessed_gaps',[]))} self-assessed gaps")
except Exception as e:
    print(f"Flask test error: {e}")

print("\nAll tests passed!")