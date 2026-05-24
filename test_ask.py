"""Test the ask/knowledge search functionality end-to-end."""
import json
from pathlib import Path

# Import the blueprint factory and test the internal search
from web.ask import create_ask_blueprint

# Create blueprint without agent — it should fall back to persist files
bp = create_ask_blueprint(agent=None)

# Check if persist files exist
kg_path = Path('state/knowledge_graph.json')
mem_path = Path('state/memories.json')
print(f"Knowledge graph exists: {kg_path.exists()}")
print(f"Memories file exists: {mem_path.exists()}")

if kg_path.exists():
    data = json.loads(kg_path.read_text())
    facts = data.get('facts', {})
    print(f"Facts in knowledge graph: {len(facts)}")

if mem_path.exists():
    data = json.loads(mem_path.read_text())
    eps = data if isinstance(data, list) else data.get('episodes', [])
    print(f"Episodes in memories: {len(eps)}")

# Now test via Flask test client
from flask import Flask
app = Flask(__name__, template_folder='web/templates')
app.register_blueprint(bp)

with app.test_client() as client:
    # Test 1: Ask page loads
    resp = client.get('/ask')
    print(f"\n=== GET /ask: status {resp.status_code} ===")
    
    # Test 2: Query endpoint
    resp = client.post('/ask/query', 
                       json={'question': 'what have I learned'},
                       content_type='application/json')
    print(f"\n=== POST /ask/query 'what have I learned': status {resp.status_code} ===")
    result = resp.get_json()
    print(f"Matched: {result.get('matched', 0)} / {result.get('total_searched', 0)}")
    for i, r in enumerate(result.get('results', [])[:5]):
        print(f"  {i+1}. {r[:90]}")
    
    # Test 3: Specific query
    resp = client.post('/ask/query',
                       json={'question': 'dream insight'},
                       content_type='application/json')
    result = resp.get_json()
    print(f"\n=== Query 'dream insight': {result.get('matched', 0)} results ===")
    for i, r in enumerate(result.get('results', [])[:3]):
        print(f"  {i+1}. {r[:90]}")
    
    # Test 4: Random endpoint
    resp = client.get('/ask/random')
    result = resp.get_json()
    print(f"\n=== Random: {result.get('total', 0)} total items ===")
    for f in result.get('facts', [])[:2]:
        print(f"  • {f[:90]}")

print("\n=== All tests complete ===")